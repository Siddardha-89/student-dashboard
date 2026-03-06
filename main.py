from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import uvicorn
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
import sys

# Ensure local imports work
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

import models, database, ml_model

app = FastAPI(title="Student Performance Analyzer API")

# 🔥 ROOT ROUTE ADDED
@app.get("/")
def home():
    return {"message": "Student Performance Analyzer API Running Successfully"}

# Security
SECRET_KEY = "SUPER_SECRET_GOLD_ACCENT_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=database.engine)

# Password Helpers
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Login
@app.post("/login", response_model=models.Token)
def login(user_data: models.UserCreate, db: Session = Depends(database.get_db)):
    user = db.query(models.UserDB).filter(models.UserDB.username == user_data.username).first()

    if not user:
        if user_data.username == "admin" and user_data.password == "admin123":
            new_user = models.UserDB(
                username="admin",
                hashed_password=get_password_hash("admin123"),
                role="admin"
            )
            db.add(new_user)
            db.commit()
            user = new_user
        else:
            raise HTTPException(status_code=400, detail="Incorrect username or password")

    if not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

# Add Student
@app.post("/add-student", response_model=models.Student)
def add_student(student: models.StudentCreate, db: Session = Depends(database.get_db)):
    # Check if roll number already exists
    existing_student = db.query(models.StudentDB).filter(models.StudentDB.roll_no == student.roll_no).first()
    if existing_student:
        raise HTTPException(status_code=400, detail=f"Student with Roll No {student.roll_no} already exists.")
    
    db_student = models.StudentDB(**student.dict())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

# Get One Student
@app.get("/student/{roll_no}", response_model=models.Student)
def get_student(roll_no: str, db: Session = Depends(database.get_db)):
    student = db.query(models.StudentDB).filter(models.StudentDB.roll_no == roll_no).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

# Get All Students
@app.get("/students", response_model=List[models.Student])
def get_all_students(db: Session = Depends(database.get_db)):
    return db.query(models.StudentDB).all()

# Delete Student
@app.delete("/student/{roll_no}")
def delete_student(roll_no: str, db: Session = Depends(database.get_db)):
    student = db.query(models.StudentDB).filter(models.StudentDB.roll_no == roll_no).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()
    return {"message": "Student deleted"}

# ML Prediction APIs
@app.post("/predict-risk")
def predict_risk_api(student_data: dict):
    return ml_model.predict_risk(student_data['gpa'], student_data['attendance'])

@app.post("/predict-placement")
def predict_placement_api(student_data: dict):
    return ml_model.predict_placement(
        student_data['gpa'],
        student_data['coding_score'],
        student_data['communication_score'],
        student_data['projects_count']
    )

@app.get("/suggestions/{roll_no}")
def get_suggestions(roll_no: str, db: Session = Depends(database.get_db)):
    student = db.query(models.StudentDB).filter(models.StudentDB.roll_no == roll_no).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return ml_model.get_improvement_suggestions(student.marks)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)