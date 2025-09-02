import os
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import passlib.hash as _hash
from jose import JWTError, jwt
import sqlalchemy.orm as _orm
from sqlalchemy.orm import joinedload 
from . import models, database, schemas, services

def get_user_by_email(db: _orm.Session, email: str):
    """
    Queries the database to find a user by their email address.
    """
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: _orm.Session, user: schemas.UserCreate):
    """
    Creates a new user in the database with a hashed password.
    """
    # Hash the user's password for security
    hashed_password = _hash.bcrypt.hash(user.password)
    # Create a new User database model instance
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    # Add the new user to the session and commit to the database
    db.add(db_user)
    db.commit()
    db.refresh(db_user) # Refresh to get the new ID from the DB
    return db_user

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

def authenticate_user(db, email, password):
    user = get_user_by_email(db, email=email)
    if not user:
        return False
    if not user.verify_password(password):
        return False
    return user

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# This tells FastAPI where to look for the token (in the Authorization header)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme), db: _orm.Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

def create_patient(db: _orm.Session, patient: schemas.PatientCreate):
    """
    Creates a new patient record in the database.
    """
    db_patient = models.Patient(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

def create_prediction(db: _orm.Session, prediction: schemas.PredictionCreate, user_id: int, patient_id: int):
    """
    Creates a new prediction record in the database, linked to a user and a patient.
    """
    db_prediction = models.Prediction(
        **prediction.dict(), 
        owner_id=user_id, 
        patient_record_id=patient_id
    )
    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)
    return db_prediction

# Find the get_predictions_for_user function and update it
def get_predictions_for_user(db: _orm.Session, user_id: int):
    """
    Queries the database for all predictions made by a specific user.
    """
    return (
        db.query(models.Prediction)
        .options(joinedload(models.Prediction.patient))  # eager load related patient
        .filter(models.Prediction.owner_id == user_id)
        .order_by(models.Prediction.prediction_timestamp.desc())
        .all()
    )