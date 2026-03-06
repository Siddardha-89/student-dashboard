from sqlalchemy import Column, Integer, String, Float, JSON, Boolean
import database
from database import Base
from pydantic import BaseModel
from typing import List, Optional

# SQLAlchemy Models
class StudentDB(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    roll_no = Column(String, unique=True, index=True)
    department = Column(String)
    marks = Column(JSON)  # Subject-wise marks {math: 90, physics: 85}
    attendance = Column(Float)
    internal_marks = Column(Float)
    prev_gpa = Column(Float)
    backlog_history = Column(Integer)
    coding_score = Column(Float)
    communication_score = Column(Float)
    projects_count = Column(Integer)

class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)  # 'admin' or 'student'

# Pydantic Schemas
class StudentBase(BaseModel):
    name: str
    roll_no: str
    department: str
    marks: dict
    attendance: float
    internal_marks: float
    prev_gpa: float
    backlog_history: int
    coding_score: float
    communication_score: float
    projects_count: int

class StudentCreate(StudentBase):
    pass

class Student(StudentBase):
    id: int

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str
    password: str
    role: str

class User(BaseModel):
    username: str
    role: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
