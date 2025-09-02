import uuid
from pathlib import Path
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
import sqlalchemy.orm as orm
from . import models, database, schemas, services, ml_services

# This command tells SQLAlchemy to create all the tables
models.Base.metadata.create_all(bind=database.engine)

# Create a directory for uploads if it doesn't exist
Path("uploads").mkdir(exist_ok=True)

# Initialize the FastAPI app
app = FastAPI(title="Brain Tumor Detection API")

# CORS Middleware
origins = [
    "http://localhost",
    "http://localhost:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.on_event("startup")
def on_startup():
    database.Base.metadata.create_all(bind=database.engine)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Brain Tumor Detection API"}

@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: orm.Session = Depends(database.get_db)):
    user = services.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = services.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(services.get_current_user)):
    return current_user

# --- PREDICT ENDPOINT (CHANGED) ---
@app.post("/predict/image") # Removed response_model to allow for multiple response types
async def predict_image(
    patient_id: str = Form(...),
    name: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    force_predict: bool = Form(False), # Added force_predict flag
    image: UploadFile = File(...),
    db: orm.Session = Depends(database.get_db),
    current_user: models.User = Depends(services.get_current_user),
):
    image_bytes = await image.read()
    try:
        # Pass the force_predict flag to the service
        inference_result = ml_services.run_inference(image_bytes, force_predict=force_predict)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Check if the result is a warning and return it directly
    if "warning" in inference_result:
        return inference_result

    # If it's a full prediction, proceed as before
    unique_id = uuid.uuid4()
    image_filename = f"{unique_id}.png"
    image_path = Path("uploads") / image_filename
    with open(image_path, "wb") as f:
        f.write(inference_result["overlay_image_bytes"])
    
    patient_schema = schemas.PatientCreate(patient_id=patient_id, name=name, age=age, gender=gender)
    db_patient = services.create_patient(db, patient_schema)

    prediction_schema = schemas.PredictionCreate(
        predicted_class=inference_result["prediction"]["class"],
        confidence=inference_result["prediction"]["confidence"],
        reason=inference_result["reason"],
        image_url=str(image_path)
    )
    return services.create_prediction(
        db, 
        prediction=prediction_schema, 
        user_id=current_user.id, 
        patient_id=db_patient.id
    )

@app.post("/users", response_model=schemas.User)
def create_user_endpoint(user: schemas.UserCreate, db: orm.Session = Depends(database.get_db)):
    db_user = services.get_user_by_email(db=db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return services.create_user(db=db, user=user)

@app.get("/users/me/history", response_model=List[schemas.PredictionWithPatient])
def read_user_history(
    current_user: models.User = Depends(services.get_current_user), 
    db: orm.Session = Depends(database.get_db)
):
    return services.get_predictions_for_user(db, user_id=current_user.id)

