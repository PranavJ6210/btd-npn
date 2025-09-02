import datetime as _dt
import sqlalchemy as _sql
import sqlalchemy.orm as _orm
import passlib.hash as _hash

# We import Base from database.py now
from .database import Base

# We no longer need this line: Base = declarative_base()

# CORRECTED LINE 1: Inherit from Base
class User(Base):
    """Represents a user in the database."""
    __tablename__ = "users"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    email = _sql.Column(_sql.String, unique=True, index=True, nullable=False)
    hashed_password = _sql.Column(_sql.String, nullable=False)
    predictions = _orm.relationship("Prediction", back_populates="owner")

    def verify_password(self, password: str):
        return _hash.bcrypt.verify(password, self.hashed_password)

# CORRECTED LINE 2: Inherit from Base
class Patient(Base):
    """Represents patient metadata."""
    __tablename__ = "patients"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    patient_id = _sql.Column(_sql.String, index=True, nullable=False)
    name = _sql.Column(_sql.String, nullable=False)
    age = _sql.Column(_sql.Integer, nullable=False)
    gender = _sql.Column(_sql.String, nullable=False)
    predictions = _orm.relationship("Prediction", back_populates="patient")

# CORRECTED LINE 3: Inherit from Base
class Prediction(Base):
    """Represents a single model prediction and its associated data."""
    __tablename__ = "predictions"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    predicted_class = _sql.Column(_sql.String, nullable=False)
    confidence = _sql.Column(_sql.Float, nullable=False)
    reason = _sql.Column(_sql.String, nullable=True)
    image_url = _sql.Column(_sql.String, nullable=False)
    prediction_timestamp = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)
    owner_id = _sql.Column(_sql.Integer, _sql.ForeignKey("users.id"))
    patient_record_id = _sql.Column(_sql.Integer, _sql.ForeignKey("patients.id"))
    owner = _orm.relationship("User", back_populates="predictions")
    patient = _orm.relationship("Patient", back_populates="predictions")