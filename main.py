from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import uvicorn
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

import models
import database
import ml_model


app = FastAPI(title="Student Performance Analyzer API")


# ================= WEBSITE =================

@app.get("/")
def home():
    return FileResponse(
        os.path.join(BASE_DIR, "index.html")
    )


@app.get("/login.html")
def login_page():
    return FileResponse(
        os.path.join(BASE_DIR, "login.html")
    )


@app.get("/dashboard.html")
def dashboard_page():
    return FileResponse(
        os.path.join(BASE_DIR, "dashboard.html")
    )


@app.get("/admin.html")
def admin_page():
    return FileResponse(
        os.path.join(BASE_DIR, "admin.html")
    )


@app.get("/report.html")
def report_page():
    return FileResponse(
        os.path.join(BASE_DIR, "report.html")
    )


@app.get("/style.css")
def style():
    return FileResponse(
        os.path.join(BASE_DIR, "style.css")
    )


@app.get("/script.js")
def script():
    return FileResponse(
        os.path.join(BASE_DIR, "script.js")
    )


# ================= SECURITY =================

SECRET_KEY = "SUPER_SECRET_GOLD_ACCENT_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# ================= CORS =================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ================= DATABASE =================

models.Base.metadata.create_all(
    bind=database.engine
)


# ================= PASSWORD =================

def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(
        plain_password,
        hashed_password
    )


# ================= JWT TOKEN =================

def create_access_token(data: dict):

    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({
        "exp": expire
    })

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# ================= LOGIN =================

@app.post(
    "/login",
    response_model=models.Token
)
def login(user_data: models.UserCreate):

    if (
        user_data.username == "admin"
        and user_data.password == "admin123"
    ):

        access_token = create_access_token(
            data={
                "sub": "admin",
                "role": "admin"
            }
        )

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    raise HTTPException(
        status_code=400,
        detail="Incorrect username or password"
    )


# ================= STUDENTS =================

@app.post(
    "/add-student",
    response_model=models.Student
)
def add_student(
    student: models.StudentCreate,
    db: Session = Depends(database.get_db)
):

    existing_student = db.query(
        models.StudentDB
    ).filter(
        models.StudentDB.roll_no == student.roll_no
    ).first()

    if existing_student:
        raise HTTPException(
            status_code=400,
            detail=f"Student with Roll No {student.roll_no} already exists."
        )

    db_student = models.StudentDB(
        **student.dict()
    )

    db.add(db_student)
    db.commit()
    db.refresh(db_student)

    return db_student


@app.get(
    "/student/{roll_no}",
    response_model=models.Student
)
def get_student(
    roll_no: str,
    db: Session = Depends(database.get_db)
):

    student = db.query(
        models.StudentDB
    ).filter(
        models.StudentDB.roll_no == roll_no
    ).first()

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    return student


@app.get(
    "/students",
    response_model=List[models.Student]
)
def get_all_students(
    db: Session = Depends(database.get_db)
):

    return db.query(
        models.StudentDB
    ).all()


@app.delete(
    "/student/{roll_no}"
)
def delete_student(
    roll_no: str,
    db: Session = Depends(database.get_db)
):

    student = db.query(
        models.StudentDB
    ).filter(
        models.StudentDB.roll_no == roll_no
    ).first()

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    db.delete(student)
    db.commit()

    return {
        "message": "Student deleted"
    }


# ================= AI / ML =================

@app.post("/predict-risk")
def predict_risk_api(
    student_data: dict
):

    return ml_model.predict_risk(
        student_data["gpa"],
        student_data["attendance"]
    )


@app.post("/predict-placement")
def predict_placement_api(
    student_data: dict
):

    return ml_model.predict_placement(
        student_data["gpa"],
        student_data["coding_score"],
        student_data["communication_score"],
        student_data["projects_count"]
    )


@app.get(
    "/suggestions/{roll_no}"
)
def get_suggestions(
    roll_no: str,
    db: Session = Depends(database.get_db)
):

    student = db.query(
        models.StudentDB
    ).filter(
        models.StudentDB.roll_no == roll_no
    ).first()

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    return ml_model.get_improvement_suggestions(
        student.marks
    )


# ================= RUN =================

if __name__ == "__main__":

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001
    )
