import torch
import torch.nn as nn
import cv2
import numpy as np
import json
from torchvision import models, transforms
from pathlib import Path
from .utils_cam import GradCAM, heatmap_to_circle, overlay_cam

# --- Configuration ---
IM_SIZE = 384
IMNET_MEAN = [0.485, 0.456, 0.406]
IMNET_STD = [0.229, 0.224, 0.225]
MODEL_PATH = Path("outputs/model_calibrated.pt")
LABEL_MAP_PATH = Path("outputs/label_map.json")
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# --- Gating Logic Thresholds ---
CONF_THRESH = 0.55
CAM_AREA_THRESH = 0.005
CAM_THRESHOLD = 0.35

# --- Model Loading (Singleton Pattern) ---
class ModelSingleton:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            print("Loading model for the first time...")
            cls._instance = super(ModelSingleton, cls).__new__(cls)
            
            checkpoint = torch.load(MODEL_PATH, map_location=DEVICE)
            
            with open(LABEL_MAP_PATH, "r") as f:
                cls.classes = json.load(f)["classes"]
            
            num_classes = len(cls.classes)
            
            model = models.resnet50()
            model.fc = nn.Linear(model.fc.in_features, num_classes)
            model.load_state_dict(checkpoint['model'])
            model.to(DEVICE)
            model.eval()

            cls.model = model
            cls.T = float(checkpoint.get('T', 1.0))
            print("Model loaded successfully.")
        return cls._instance

# --- Heuristic MRI Validation (CHANGED) ---
def is_valid_mri(bgr: np.ndarray):
    """
    Heuristic check for brain MRI-like images. 
    Returns a warning string if a check fails, otherwise returns None.
    """
    if bgr is None: return "Invalid image data."
    H, W = bgr.shape[:2]
    if H < 128 or W < 128: return "Warning: Image is very small (<128px)."

    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    sat_mean = hsv[..., 1].mean()
    if sat_mean > 20: return "Warning: Image has high color saturation, may not be a standard MRI."

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    
    brightness = gray.mean()
    if brightness < 5: return "Warning: Image is extremely dark."

    black_frac = (gray < 20).mean()
    if black_frac < 0.25: return "Warning: Image may lack the typical black background of an MRI."

    y0, y1 = int(0.2 * H), int(0.8 * H)
    x0, x1 = int(0.2 * W), int(0.8 * W)
    center_brightness = gray[y0:y1, x0:x1].mean()
    if center_brightness < 40: return "Warning: The center of the image is unusually dark."
    
    return None # Return None if all checks pass

# --- Preprocessing ---
def preprocess_bgr(bgr: np.ndarray):
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    tfm = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((IM_SIZE, IM_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(IMNET_MEAN, IMNET_STD),
    ])
    return tfm(rgb).unsqueeze(0)

# --- Main Inference Function (CHANGED) ---
def run_inference(image_bytes: bytes, force_predict: bool = False):
    # 1. Decode and Ensure 3-Channel BGR
    arr = np.frombuffer(image_bytes, np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
    if bgr is None: raise ValueError("Invalid image data")
    
    if bgr.ndim == 2: bgr = cv2.cvtColor(bgr, cv2.COLOR_GRAY2BGR)
    if bgr.shape[2] == 4: bgr = cv2.cvtColor(bgr, cv2.COLOR_BGRA2BGR)

    # 2. Run heuristic check (if not forced)
    if not force_predict:
        warning_message = is_valid_mri(bgr)
        if warning_message:
            # If there's a warning, return it immediately
            return {"warning": warning_message}

    # 3. Load model and run prediction
    model_instance = ModelSingleton()
    model, T, classes = model_instance.model, model_instance.T, model_instance.classes
    tens = preprocess_bgr(bgr).to(DEVICE)
    
    with torch.no_grad():
        logits = model(tens) / T
        probs = torch.softmax(logits, dim=1)[0].cpu().numpy()
        pred_idx = int(np.argmax(probs))
        pred_label = classes[pred_idx]
        confidence = float(probs[pred_idx])

    # 4. Generate Grad-CAM
    cam = GradCAM(model, target_layer_name='layer4')
    heatmap = cam(tens, class_idx=pred_idx)
    H0, W0 = bgr.shape[:2]
    heatmap_full = cv2.resize(heatmap, (W0, H0), interpolation=cv2.INTER_LINEAR)

    # 5. Apply "No-Tumor" Gating Logic
    cam_mask = (heatmap_full > CAM_THRESHOLD).astype(np.uint8)
    cam_area_frac = cam_mask.sum() / cam_mask.size
    
    pred_is_no_tumor = "no" in pred_label.lower()
    is_final_no_tumor = pred_is_no_tumor or (confidence < CONF_THRESH) or (cam_area_frac < CAM_AREA_THRESH)
    final_label = "no_tumor" if is_final_no_tumor else pred_label
    
    # 6. Construct Reason and Overlay Image
    reason = f"Model focus consistent with '{final_label}' features."
    if is_final_no_tumor and not pred_is_no_tumor:
        reason_detail = 'low confidence' if confidence < CONF_THRESH else 'tiny CAM area'
        reason += f" (Flagged as no_tumor due to {reason_detail})"

    overlay_img = overlay_cam(bgr, heatmap_full, alpha=0.35)
    circle, _ = heatmap_to_circle(cv2.resize(heatmap, (IM_SIZE, IM_SIZE)), threshold=CAM_THRESHOLD)
    
    cx = int(circle[0] * (W0 / IM_SIZE))
    cy = int(circle[1] * (H0 / IM_SIZE))
    r  = int(circle[2] * ((W0 + H0) / (2 * IM_SIZE)))
    circle_color = (0, 255, 0) if is_final_no_tumor else (0, 0, 255)
    
    if r > 0:
        cv2.circle(overlay_img, (cx, cy), r, circle_color, thickness=3)

    _, buf = cv2.imencode(".png", overlay_img)
    overlay_bytes = buf.tobytes()

    # 7. Return the final, robust result
    return {
        "prediction": {"class": final_label, "confidence": round(confidence, 4)},
        "reason": reason,
        "overlay_image_bytes": overlay_bytes,
    }