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


class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class PaymentMethod(str, Enum):
    CASH = "cash"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"

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


class PaymentCreate(BaseModel):
    amount_in_cents: int
    currency: str
    status: PaymentStatus = PaymentStatus.PENDING
    payment_method: PaymentMethod
    student_id: int


class PaymentUpdate(BaseModel):
    amount_in_cents: int | None = None
    currency: str | None = None
    status: PaymentStatus | None = None
    payment_method: PaymentMethod | None = None
    student_id: int | None = None


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount_in_cents: int
    currency: str
    status: PaymentStatus
    payment_method: PaymentMethod
    student_id: int
    created_at: datetime
    updated_at: datetime


class PaymentAllocationCreate(BaseModel):
    payment_id: int
    invoice_id: int
    amount_in_cents: int


class PaymentAllocationUpdate(BaseModel):
    amount_in_cents: int | None = None


class PaymentAllocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    payment_id: int
    invoice_id: int
    amount_in_cents: int
    created_at: datetime


class BalanceResponse(BaseModel):
    total_invoiced_cents: int
    total_paid_cents: int
    total_pending_cents: int
    currency: str | None
    invoices: list[InvoiceResponse]
    payments: list[PaymentResponse]


class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    school_id: int | None = None
    is_admin: bool = False


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = None
    school_id: int | None = None
    is_admin: bool | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    school_id: int | None
    is_admin: bool
    created_at: datetime
    updated_at: datetime
