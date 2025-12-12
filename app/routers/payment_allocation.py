from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import PaymentAllocation, User
from app.dependencies import get_db, get_current_active_user
from app.schemas import (
    PaymentAllocationCreate,
    PaymentAllocationUpdate,
    PaymentAllocationResponse,
    PaginatedResponse,
)
from app.services import payment_allocation as allocation_service
from app.services import payment as payment_service
from app.services import invoice as invoice_service

router = APIRouter(
    prefix="/payment-allocation",
    tags=["payment-allocation"],
)


@router.get("/", response_model=PaginatedResponse[PaymentAllocationResponse])
def list_allocations(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Returns a paginated list of payment allocations."""
    if current_user.is_admin:
        items, total = allocation_service.get_allocations_with_count(db, offset=offset, limit=limit)
    else:
        items, total = allocation_service.get_allocations_by_school_with_count(
            db, current_user.school_id, offset=offset, limit=limit
        )
    pages = (total + limit - 1) // limit if limit > 0 else 0
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset, pages=pages)


@router.get("/{allocation_id}", response_model=PaymentAllocationResponse)
def get_allocation(
    allocation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Returns the payment allocation details."""
    allocation = allocation_service.get_allocation_by_id_for_user(db, allocation_id, current_user)
    if allocation is None:
        raise HTTPException(status_code=404, detail="Payment allocation not found")
    return allocation


@router.post("/", response_model=PaymentAllocationResponse, status_code=201)
def create_allocation(
    allocation_data: PaymentAllocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Creates a new payment allocation and updates invoice status."""
    payment = payment_service.get_payment_by_id_for_user(db, allocation_data.payment_id, current_user)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")

    invoice = invoice_service.get_invoice_by_id_for_user(db, allocation_data.invoice_id, current_user)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")

    now = datetime.now()
    allocation = PaymentAllocation(
        payment_id=allocation_data.payment_id,
        invoice_id=allocation_data.invoice_id,
        amount_in_cents=allocation_data.amount_in_cents,
        created_at=now,
    )
    created_allocation = allocation_service.create_allocation(db, allocation)

    allocation_service.update_invoice_status_from_payments(db, invoice)

    return created_allocation


@router.put("/{allocation_id}", response_model=PaymentAllocationResponse)
def update_allocation(
    allocation_id: int,
    allocation_data: PaymentAllocationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Updates an existing payment allocation and updates invoice status."""
    allocation = allocation_service.get_allocation_by_id_for_user(db, allocation_id, current_user)
    if allocation is None:
        raise HTTPException(status_code=404, detail="Payment allocation not found")

    updated_allocation = allocation_service.update_allocation(db, allocation, allocation_data)

    invoice = invoice_service.get_invoice_by_id(db, allocation.invoice_id)
    if invoice:
        allocation_service.update_invoice_status_from_payments(db, invoice)

    return updated_allocation


@router.delete("/{allocation_id}", status_code=204)
def delete_allocation(
    allocation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Deletes a payment allocation and updates invoice status."""
    allocation = allocation_service.get_allocation_by_id_for_user(db, allocation_id, current_user)
    if allocation is None:
        raise HTTPException(status_code=404, detail="Payment allocation not found")

    invoice_id = allocation.invoice_id
    allocation_service.delete_allocation(db, allocation)

    invoice = invoice_service.get_invoice_by_id(db, invoice_id)
    if invoice:
        allocation_service.update_invoice_status_from_payments(db, invoice)
