import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Load environment variables from a .env file
load_dotenv()

# Get the database URL from the environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# Create the SQLAlchemy engine, which is the entry point to our database
engine = create_engine(DATABASE_URL)

# Each instance of the SessionLocal class will be a database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# We will inherit from this class to create each of the ORM models.
Base = declarative_base()

def get_db():
    """
    Dependency function to get a DB session for each request.
    Ensures the session is closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()