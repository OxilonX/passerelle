from datetime import date
from enum import Enum
from typing import Optional

from sqlalchemy import CheckConstraint,ForeignKey,Column,Integer
from sqlmodel import Field, SQLModel


class InternshipStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in progress"
    COMPLETED = "completed"


class SupervisorType(str, Enum):
    ACADEMIC = "academic"
    COMPANY = "company"


class Student(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    registration_number: str = Field(unique=True, index=True)
    last_name: str
    first_name: str
    date_of_birth: date
    address: str
    email: str


class Company(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    identifier: str = Field(unique=True, index=True)
    company_name: str = Field(index=True)
    address: str
    industry: str
    contact: str


class Supervisor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    last_name: str
    first_name: str
    supervisor_type: SupervisorType
    company_id: Optional[int] = Field(default=None, foreign_key="company.id")


class Internship(SQLModel, table=True):
    __table_args__ = (CheckConstraint("end_date >= start_date", name="ck_dates"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    topic: str
    start_date: date
    end_date: date
    description: str
    status: InternshipStatus = Field(default=InternshipStatus.PENDING, index=True)
    student_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("student.id", ondelete="CASCADE"), nullable=False
        )
    )
    company_id: int = Field(foreign_key="company.id")
    academic_supervisor_id: int = Field(foreign_key="supervisor.id")
    company_supervisor_id: int = Field(foreign_key="supervisor.id")
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True)
    password_hash: str