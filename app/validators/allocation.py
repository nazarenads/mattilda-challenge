"""Validation rules for payment allocations."""

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models import Payment, Invoice, PaymentAllocation, PaymentStatus, InvoiceStatus


class AllocationValidationError(HTTPException):
    """Raised when allocation validation fails."""

    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)


def get_payment_allocated_amount(db: Session, payment_id: int) -> int:
    """Get total amount already allocated from this payment."""
    result = (
        db.query(func.coalesce(func.sum(PaymentAllocation.amount_in_cents), 0))
        .filter(PaymentAllocation.payment_id == payment_id)
        .scalar()
    )
    return int(result)


def validate_allocation_create(
    db: Session,
    payment: Payment,
    invoice: Invoice,
    amount_in_cents: int,
) -> None:
    """
    Validate allocation creation. Raises AllocationValidationError if invalid.

    Note: Overpayments to invoices ARE allowed (allocating more than invoice balance).
    This is a valid business case where a parent pays more than owed.
    """
    # Rule 1: Amount must be positive
    if amount_in_cents <= 0:
        raise AllocationValidationError("Allocation amount must be positive")

    # Rule 2: Cannot allocate from non-completed payment
    if payment.status != PaymentStatus.COMPLETED.value:
        raise AllocationValidationError(
            f"Cannot allocate from payment with status '{payment.status}'. "
            "Payment must be completed."
        )

    # Rule 3: Cannot allocate to cancelled invoice
    if invoice.status == InvoiceStatus.CANCELLED.value:
        raise AllocationValidationError("Cannot allocate to a cancelled invoice")

    # Rule 4: Currency must match
    if payment.currency != invoice.currency:
        raise AllocationValidationError(
            f"Currency mismatch: payment is {payment.currency}, "
            f"invoice is {invoice.currency}"
        )

    # Rule 5: Cannot allocate more than payment's available amount
    already_allocated = get_payment_allocated_amount(db, payment.id)
    available = payment.amount_in_cents - already_allocated
    if amount_in_cents > available:
        raise AllocationValidationError(
            f"Allocation amount ({amount_in_cents}) exceeds available payment "
            f"balance ({available}). Payment total: {payment.amount_in_cents}, "
            f"already allocated: {already_allocated}"
        )

    # NOTE: We intentionally DO NOT validate against invoice remaining balance.
    # Overpayments are allowed - the invoice will be marked as PAID when
    # total allocations >= invoice amount.


def validate_allocation_update(
    db: Session,
    allocation: PaymentAllocation,
    new_amount_in_cents: int | None,
) -> None:
    """
    Validate allocation update.

    Note: Overpayments to invoices ARE allowed (same as create).
    """
    if new_amount_in_cents is None:
        return

    if new_amount_in_cents <= 0:
        raise AllocationValidationError("Allocation amount must be positive")

    payment = allocation.payment

    # Check payment available (excluding current allocation)
    already_allocated = get_payment_allocated_amount(db, payment.id)
    current_allocation = allocation.amount_in_cents
    available = payment.amount_in_cents - already_allocated + current_allocation

    if new_amount_in_cents > available:
        raise AllocationValidationError(
            f"New amount ({new_amount_in_cents}) exceeds available payment balance ({available})"
        )

    # NOTE: We intentionally DO NOT validate against invoice remaining balance.
    # Overpayments are allowed.
