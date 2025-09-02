from pydantic import BaseModel
import datetime as _dt

# --- Base Schemas ---
# These have fields that are shared when creating or reading data.

class _UserBase(BaseModel):
    email: str

class _PatientBase(BaseModel):
    patient_id: str
    name: str
    age: int
    gender: str

class _PredictionBase(BaseModel):
    predicted_class: str
    confidence: float
    reason: str
    image_url: str

# --- Schemas for Creating Data ---
# These are used when a user sends data to the API (e.g., signing up).

class UserCreate(_UserBase):
    password: str

class PatientCreate(_PatientBase):
    pass # No extra fields needed for creation

class PredictionCreate(_PredictionBase):
    pass # No extra fields needed for creation

# --- Schemas for Reading Data ---
# These define the shape of the data when the API returns it to the user.
# The password field is intentionally excluded for security.

class User(_UserBase):
    id: int
    class Config:
        orm_mode = True # Helps Pydantic work with our SQLAlchemy models

class Patient(_PatientBase):
    id: int
    class Config:
        orm_mode = True

class Prediction(_PredictionBase):
    id: int
    owner_id: int
    patient_record_id: int
    prediction_timestamp: _dt.datetime
    class Config:
        orm_mode = True

class PredictionWithPatient(Prediction):
    patient: Patient

    class Config:
        orm_mode = True