"""
Pydantic schemas.

Define your Pydantic models/schemas here for request/response validation.
"""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
    pages: int


class SchoolCreate(BaseModel):
    name: str
    country: str
    tax_id: str


class SchoolUpdate(BaseModel):
    name: str | None = None
    country: str | None = None
    tax_id: str | None = None


class SchoolResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    country: str
    tax_id: str
    created_at: datetime
    updated_at: datetime


class StudentCreate(BaseModel):
    name: str
    email: EmailStr
    school_id: int


class StudentUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    school_id: int | None = None


class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    school_id: int
    created_at: datetime
    updated_at: datetime


class InvoiceCreate(BaseModel):
    invoice_number: str
    amount: float
    status: str = "pending"
    issue_date: datetime
    due_date: datetime
    description: str | None = None
    student_id: int


class InvoiceUpdate(BaseModel):
    invoice_number: str | None = None
    amount: float | None = None
    status: str | None = None
    issue_date: datetime | None = None
    due_date: datetime | None = None
    description: str | None = None
    student_id: int | None = None


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_number: str
    amount: float
    status: str
    issue_date: datetime
    due_date: datetime
    description: str | None
    student_id: int
    created_at: datetime
    updated_at: datetime
