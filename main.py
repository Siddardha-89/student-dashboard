from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import List
import uvicorn
from datetime import datetime, timedelta
from jose import jwt
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

import models
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


# ================= CORS =================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ================= STUDENT STORAGE =================

students_store = {}


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


# ================= ADD STUDENT =================

@app.post(
    "/add-student",
    response_model=models.Student
)
def add_student(student: models.StudentCreate):

    roll_no = student.roll_no

    if roll_no in students_store:

        raise HTTPException(
            status_code=400,
            detail=f"Student with Roll No {roll_no} already exists."
        )

    new_id = len(students_store) + 1

    student_data = student.dict()

    student_data["id"] = new_id

    students_store[roll_no] = student_data

    return student_data


# ================= GET ONE STUDENT =================

@app.get(
    "/student/{roll_no}",
    response_model=models.Student
)
def get_student(roll_no: str):

    student = students_store.get(roll_no)

    if student is None:

        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    return student


# ================= GET ALL STUDENTS =================

@app.get(
    "/students",
    response_model=List[models.Student]
)
def get_all_students():

    return list(students_store.values())


# ================= DELETE STUDENT =================

@app.delete("/student/{roll_no}")
def delete_student(roll_no: str):

    if roll_no not in students_store:

        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    del students_store[roll_no]

    return {
        "message": "Student deleted successfully"
    }


# ================= AI / ML =================

@app.post("/predict-risk")
def predict_risk_api(student_data: dict):

    try:

        return ml_model.predict_risk(
            student_data["gpa"],
            student_data["attendance"]
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Risk prediction error: {str(e)}"
        )


@app.post("/predict-placement")
def predict_placement_api(student_data: dict):

    try:

        return ml_model.predict_placement(
            student_data["gpa"],
            student_data["coding_score"],
            student_data["communication_score"],
            student_data["projects_count"]
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Placement prediction error: {str(e)}"
        )


# ================= SUGGESTIONS =================

@app.get(
    "/suggestions/{roll_no}"
)
def get_suggestions(roll_no: str):

    student = students_store.get(roll_no)

    if student is None:

        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    try:

        return ml_model.get_improvement_suggestions(
            student["marks"]
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Suggestion error: {str(e)}"
        )


# ================= HEALTH CHECK =================

@app.get("/health")
def health_check():

    return {
        "status": "online",
        "message": "Student Performance Analyzer API is running"
    }


# ================= RUN =================

if __name__ == "__main__":

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001
    )
