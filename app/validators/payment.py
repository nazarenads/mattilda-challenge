"""Validation rules for payment modifications."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models import Payment, PaymentStatus, PaymentAllocation


class PaymentValidationError(HTTPException):
    """Raised when payment validation fails."""

    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)


def validate_payment_update(
    db: Session,
    payment: Payment,
    new_status: str | None = None,
    new_amount: int | None = None,
) -> None:
    """Validate payment updates."""
    has_allocations = (
        db.query(PaymentAllocation)
        .filter(PaymentAllocation.payment_id == payment.id)
        .first()
        is not None
    )

    # Cannot change amount if payment has allocations
    if new_amount is not None and has_allocations:
        if new_amount != payment.amount_in_cents:
            raise PaymentValidationError(
                "Cannot modify amount of a payment that has allocations"
            )

    # Cannot change status from COMPLETED to PENDING/FAILED if has allocations
    if new_status is not None and has_allocations:
        if payment.status == PaymentStatus.COMPLETED.value:
            if new_status in [PaymentStatus.PENDING.value, PaymentStatus.FAILED.value]:
                raise PaymentValidationError(
                    f"Cannot revert a completed payment with allocations to "
                    f"'{new_status}' status"
                )


def validate_payment_delete(db: Session, payment: Payment) -> None:
    """Validate payment deletion."""
    has_allocations = (
        db.query(PaymentAllocation)
        .filter(PaymentAllocation.payment_id == payment.id)
        .first()
        is not None
    )

    if has_allocations:
        raise PaymentValidationError(
            "Cannot delete a payment that has allocations. "
            "Delete the allocations first."
        )
