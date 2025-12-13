from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import PaymentAllocation, Payment, Invoice, Student, PaymentStatus, InvoiceStatus, User
from app.schemas import PaymentAllocationUpdate


def create_allocation(db: Session, allocation: PaymentAllocation) -> PaymentAllocation:
    """Create allocation without updating invoice status. Use create_allocation_with_status_update instead."""
    db.add(allocation)
    db.commit()
    db.refresh(allocation)
    return allocation


def create_allocation_with_status_update(
    db: Session,
    payment: Payment,
    invoice: Invoice,
    amount_in_cents: int,
) -> PaymentAllocation:
    """
    Create allocation and update invoice status in a single transaction.
    Rolls back both if either fails.
    """
    try:
        now = datetime.now()
        allocation = PaymentAllocation(
            payment_id=payment.id,
            invoice_id=invoice.id,
            amount_in_cents=amount_in_cents,
            created_at=now,
        )
        db.add(allocation)
        db.flush()  # Get the ID without committing

        # Update invoice status
        _update_invoice_status_internal(db, invoice)

        db.commit()
        db.refresh(allocation)
        return allocation
    except Exception:
        db.rollback()
        raise


def get_allocation_by_id(db: Session, allocation_id: int) -> PaymentAllocation | None:
    return db.query(PaymentAllocation).filter(PaymentAllocation.id == allocation_id).first()


def get_allocation_by_id_for_user(db: Session, allocation_id: int, user: User) -> PaymentAllocation | None:
    """Get payment allocation by ID, filtered by user's school access."""
    query = db.query(PaymentAllocation).filter(PaymentAllocation.id == allocation_id)
    if not user.is_admin:
        query = (
            query
            .join(Invoice)
            .join(Student)
            .filter(Student.school_id == user.school_id)
        )
    return query.first()


def get_allocations(db: Session, offset: int = 0, limit: int = 100) -> list[PaymentAllocation]:
    return db.query(PaymentAllocation).offset(offset).limit(limit).all()


def get_allocations_with_count(
    db: Session, offset: int = 0, limit: int = 100
) -> tuple[list[PaymentAllocation], int]:
    total = db.query(PaymentAllocation).count()
    items = db.query(PaymentAllocation).offset(offset).limit(limit).all()
    return items, total


def get_allocations_by_school_with_count(
    db: Session, school_id: int, offset: int = 0, limit: int = 100
) -> tuple[list[PaymentAllocation], int]:
    query = (
        db.query(PaymentAllocation)
        .join(Invoice, PaymentAllocation.invoice_id == Invoice.id)
        .join(Student, Invoice.student_id == Student.id)
        .filter(Student.school_id == school_id)
    )
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    return items, total


def update_allocation(
    db: Session, allocation: PaymentAllocation, allocation_data: PaymentAllocationUpdate
) -> PaymentAllocation:
    """Update allocation without updating invoice status. Use update_allocation_with_status_update instead."""
    update_data = allocation_data.model_dump(exclude_unset=True, mode="json")
    for field, value in update_data.items():
        setattr(allocation, field, value)
    db.commit()
    db.refresh(allocation)
    return allocation


def update_allocation_with_status_update(
    db: Session,
    allocation: PaymentAllocation,
    allocation_data: PaymentAllocationUpdate,
) -> PaymentAllocation:
    """
    Update allocation and update invoice status in a single transaction.
    Rolls back both if either fails.
    """
    try:
        update_data = allocation_data.model_dump(exclude_unset=True, mode="json")
        for field, value in update_data.items():
            setattr(allocation, field, value)
        db.flush()

        # Update invoice status
        invoice = allocation.invoice
        _update_invoice_status_internal(db, invoice)

        db.commit()
        db.refresh(allocation)
        return allocation
    except Exception:
        db.rollback()
        raise


def delete_allocation(db: Session, allocation: PaymentAllocation) -> None:
    """Delete allocation without updating invoice status. Use delete_allocation_with_status_update instead."""
    db.delete(allocation)
    db.commit()


def delete_allocation_with_status_update(
    db: Session,
    allocation: PaymentAllocation,
) -> None:
    """
    Delete allocation and update invoice status in a single transaction.
    Rolls back both if either fails.
    """
    try:
        invoice = allocation.invoice
        db.delete(allocation)
        db.flush()

        # Update invoice status
        _update_invoice_status_internal(db, invoice)

        db.commit()
    except Exception:
        db.rollback()
        raise


def get_invoice_paid_amount(db: Session, invoice_id: int) -> int:
    """Sum all allocations for an invoice from completed payments only."""
    result = (
        db.query(func.coalesce(func.sum(PaymentAllocation.amount_in_cents), 0))
        .join(Payment, PaymentAllocation.payment_id == Payment.id)
        .filter(
            PaymentAllocation.invoice_id == invoice_id,
            Payment.status == PaymentStatus.COMPLETED.value
        )
        .scalar()
    )
    return int(result)


def _update_invoice_status_internal(db: Session, invoice: Invoice) -> None:
    """
    Update invoice status based on total paid amount from completed payments.
    Internal function - does NOT commit. Use within a transaction.
    """
    paid_amount = get_invoice_paid_amount(db, invoice.id)

    if paid_amount >= invoice.amount_in_cents:
        invoice.status = InvoiceStatus.PAID.value
    elif paid_amount > 0:
        invoice.status = InvoiceStatus.PARTIALLY_PAID.value
    # If paid_amount == 0, we don't change the status (could be PENDING, OVERDUE, etc.)


def update_invoice_status_from_payments(db: Session, invoice: Invoice) -> Invoice:
    """
    Update invoice status based on total paid amount from completed payments.
    This is a standalone operation that commits immediately.
    Prefer using the transactional functions (create/update/delete_allocation_with_status_update).
    """
    _update_invoice_status_internal(db, invoice)
    db.commit()
    db.refresh(invoice)
    return invoice
