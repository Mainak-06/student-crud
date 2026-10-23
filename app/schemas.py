"""Pydantic models = input validation + response shapes."""
from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


def _check_phone(v: Optional[str]) -> Optional[str]:
    if v is None:
        return v
    v = v.strip()
    digits = [c for c in v if c.isdigit()]
    if not (7 <= len(digits) <= 15) or any(c not in "0123456789+-() " for c in v):
        raise ValueError("phone must contain 7-15 digits (spaces, +, -, () allowed)")
    return v


def _check_dob(v: Optional[date]) -> Optional[date]:
    if v is not None and v >= date.today():
        raise ValueError("date_of_birth must be in the past")
    return v


class StudentBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, examples=["Aarav Sharma"])
    date_of_birth: date = Field(..., examples=["2003-05-14"])
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, examples=["+91 98765 43210"])
    course: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)
    enrollment_date: Optional[date] = None

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("name must have at least 2 characters")
        return v

    _dob = field_validator("date_of_birth")(_check_dob)
    _phone = field_validator("phone")(_check_phone)


class StudentCreate(StudentBase):
    """Used for POST and PUT (full replace). Needs email and/or phone."""

    @model_validator(mode="after")
    def _need_contact(self):
        if not self.email and not self.phone:
            raise ValueError("provide at least one contact: email or phone")
        return self


class StudentUpdate(BaseModel):
    """Used for PATCH: every field optional."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    date_of_birth: Optional[date] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    course: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)
    enrollment_date: Optional[date] = None

    _dob = field_validator("date_of_birth")(_check_dob)
    _phone = field_validator("phone")(_check_phone)


class Student(StudentBase):
    id: int


class AIQuestion(BaseModel):
    question: str = Field(..., min_length=3, max_length=500,
                          examples=["How many students are there?"])


class AIAnswer(BaseModel):
    question: str
    answer: str
    records_used: list[Student]
    model: str
