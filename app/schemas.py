"""
Pydantic schemas.

Define your Pydantic models/schemas here for request/response validation.
"""

from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

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
    identifier: str
    name: str
    email: EmailStr
    school_id: int


class StudentUpdate(BaseModel):
    identifier: str | None = None
    name: str | None = None
    email: EmailStr | None = None
    school_id: int | None = None


class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    identifier: str
    name: str
    email: str
    school_id: int
    created_at: datetime
    updated_at: datetime


class InvoiceCreate(BaseModel):
    invoice_number: str
    amount_in_cents: int
    currency: str
    status: InvoiceStatus = InvoiceStatus.PENDING
    issue_date: datetime
    due_date: datetime
    description: str | None = None
    student_id: int


class InvoiceUpdate(BaseModel):
    invoice_number: str | None = None
    amount_in_cents: int | None = None
    currency: str | None = None
    status: InvoiceStatus | None = None
    issue_date: datetime | None = None
    due_date: datetime | None = None
    description: str | None = None
    student_id: int | None = None


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_number: str
    amount_in_cents: int
    currency: str
    status: InvoiceStatus
    issue_date: datetime
    due_date: datetime
    description: str | None
    student_id: int
    created_at: datetime
    updated_at: datetime
