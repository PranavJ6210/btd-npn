import React, { useState } from "react";
import api from "../api"; // Import our authenticated API client

function PredictPage() {
  const [patientId, setPatientId] = useState("");
  const [name, setName] = useState("");
  const [age, setAge] = useState("");
  const [gender, setGender] = useState("");
  const [image, setImage] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null); // Local preview
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [warning, setWarning] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    setImage(file);
    setPreviewUrl(file ? URL.createObjectURL(file) : null); // Create local preview
    setResult(null);
    setError("");
    setWarning("");
  };

  const handleSubmit = async (isForced = false) => {
    if (!image) {
      setError("Please select an image file.");
      return;
    }

    setIsLoading(true);
    setResult(null);
    setError("");
    setWarning("");

    const formData = new FormData();
    formData.append("patient_id", patientId);
    formData.append("name", name);
    formData.append("age", age);
    formData.append("gender", gender);
    formData.append("image", image);
    formData.append("force_predict", isForced);

    try {
      const response = await api.post("/predict/image", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      if (response.data.warning) {
        setWarning(response.data.warning);
      } else {
        setResult(response.data);
      }
    } catch (err) {
      setError(
        "Prediction failed: " +
          (err.response?.data?.detail || err.message)
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", alignItems: "flex-start", gap: "20px" }}>
      {/* Form Section */}
      <div style={{ flex: 1, maxWidth: "400px" }}>
        <h2>Make a Prediction</h2>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSubmit(false);
          }}
        >
          <input
            type="text"
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
            placeholder="Patient ID"
            required
          />
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Patient Name"
            required
          />
          <input
            type="number"
            value={age}
            onChange={(e) => setAge(e.target.value)}
            placeholder="Age"
            required
          />
          <input
            type="text"
            value={gender}
            onChange={(e) => setGender(e.target.value)}
            placeholder="Gender"
            required
          />
          <input
            type="file"
            onChange={handleFileChange}
            accept="image/*"
            required
          />
          <button type="submit" disabled={isLoading || warning}>
            {isLoading ? "Predicting..." : "Get Prediction"}
          </button>
        </form>

        {warning && !isLoading && (
          <div className="prediction-result" style={{ borderColor: "orange" }}>
            <h3>Warning</h3>
            <p>{warning}</p>
            <button onClick={() => handleSubmit(true)} disabled={isLoading}>
              {isLoading ? "Predicting..." : "Confirm and Predict Anyway"}
            </button>
          </div>
        )}

        {error && <p style={{ color: "red" }}>{error}</p>}

        {result && (
          <div className="prediction-result">
            <h3>Prediction Result</h3>
            <p>
              <strong>Class:</strong> {result.predicted_class}
            </p>
            <p>
              <strong>Confidence:</strong> {result.confidence.toFixed(4)}
            </p>
            <p>
              <strong>Reason:</strong> {result.reason}
            </p>
            <img
              src={`${api.defaults.baseURL}/${result.image_url}`}
              alt="Prediction Overlay"
              style={{ maxWidth: "100%", marginTop: "20px" }}
            />
          </div>
        )}
      </div>

      {/* Image Preview Section */}
      {previewUrl && (
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column", // stack header and image vertically
            alignItems: "center",
          }}
        >
          <h2 style={{ marginBottom: "10px" }}>Uploaded Image</h2>
          <img
            src={previewUrl}
            alt="Uploaded Preview"
            style={{
              maxHeight: "100%",
              maxWidth: "350px",
              objectFit: "contain",
              border: "1px solid #ccc",
              borderRadius: "8px",
            }}
          />
        </div>
      )}
    </div>
  );
}

export default PredictPage;
