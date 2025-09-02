
# utils_cam.py
import cv2
import numpy as np
import torch
import torch.nn.functional as F

class GradCAM:
    """
    Minimal Grad-CAM for a single target layer on ResNet-like models.
    Usage:
      cam = GradCAM(model, target_layer_name='layer4')
      heatmap = cam(tensor, class_idx)  # (H, W) float32 in [0,1]
    """
    def __init__(self, model, target_layer_name='layer4'):
        self.model = model
        self.model.eval()
        self.activations = None
        self.gradients = None

        target_layer = dict([*self.model.named_modules()])[target_layer_name]
        target_layer.register_forward_hook(self._forward_hook)
        target_layer.register_full_backward_hook(self._backward_hook)

    def _forward_hook(self, module, input, output):
        self.activations = output.detach()

    def _backward_hook(self, module, grad_input, grad_output):
        self.gradients = grad_output[0].detach()

    @torch.no_grad()
    def _normalize(self, x, eps=1e-6):
        x = x - x.min()
        x = x / (x.max() + eps)
        return x

    def __call__(self, input_tensor, class_idx: int):
        """
        input_tensor: (1, 3, H, W) torch.FloatTensor
        class_idx: int
        returns heatmap: (H, W) np.float32 in [0,1]
        """
        self.model.zero_grad(set_to_none=True)
        logits = self.model(input_tensor)  # (1, C)
        score = logits[0, class_idx]
        self.model.zero_grad(set_to_none=True)
        score.backward(retain_graph=True)

        # activations: (1, Ck, h, w); gradients: (1, Ck, h, w)
        grads = self.gradients
        acts = self.activations
        weights = grads.mean(dim=(2, 3), keepdim=True)  # (1, Ck, 1, 1)

        cam = (weights * acts).sum(dim=1, keepdim=True)  # (1,1,h,w)
        cam = F.relu(cam)  # only positive
        cam = F.interpolate(cam, size=input_tensor.shape[-2:], mode='bilinear', align_corners=False)
        cam = cam[0, 0].cpu().numpy().astype(np.float32)
        return self._normalize(cam)

def heatmap_to_circle(heatmap: np.ndarray,
                      threshold: float = 0.35,
                      min_area_px: int = 50):
    """
    From a normalized heatmap [0,1], threshold and find the largest contour;
    return center (x, y) and radius r of min enclosing circle.
    Fallback: return image center with radius 0.
    """
    h, w = heatmap.shape
    hm8 = (heatmap * 255).astype(np.uint8)
    # Otsu or fixed threshold (use max of both to avoid noise)
    _, th_fixed = cv2.threshold(hm8, int(threshold * 255), 255, cv2.THRESH_BINARY)
    _, th_otsu  = cv2.threshold(hm8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    mask = cv2.bitwise_and(th_fixed, th_otsu)

    # Morphology to clean small speckles
    kernel = np.ones((3,3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return (w // 2, h // 2, 0), mask  # no circle

    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
    for c in cnts:
        area = cv2.contourArea(c)
        if area >= min_area_px:
            (cx, cy), r = cv2.minEnclosingCircle(c)
            return (int(cx), int(cy), int(r)), mask

    # If all are tiny
    (cx, cy), r = cv2.minEnclosingCircle(cnts[0])
    return (int(cx), int(cy), int(r)), mask

def draw_circle_overlay(bgr_img: np.ndarray, circle, thickness: int = 3):
    x, y, r = circle
    out = bgr_img.copy()
    if r > 0:
        cv2.circle(out, (x, y), r, (0, 0, 255), thickness)  # red circle
    return out

def overlay_cam(bgr_img: np.ndarray, heatmap: np.ndarray, alpha: float = 0.35):
    # Make a colored heatmap and blend with image
    hm8 = (heatmap * 255).astype(np.uint8)
    hm_color = cv2.applyColorMap(hm8, cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(bgr_img, 1.0, hm_color, alpha, 0)
    return overlay

def cam_reason(heatmap: np.ndarray, mask: np.ndarray, pred_label: str):
    area_frac = float((mask > 0).sum()) / float(mask.size)
    # simple, honest reason text
    return (f"Model focuses on a localized region (CAM area ≈ {area_frac*100:.1f}%). "
            f"Pattern consistent with '{pred_label}' features learned during training.")
