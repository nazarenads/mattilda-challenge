from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import School, Student, Invoice, Payment, PaymentAllocation, InvoiceStatus, PaymentStatus
from app.schemas import SchoolUpdate, BalanceResponse, InvoiceResponse, PaymentResponse


def create_school(db: Session, school: School) -> School:
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


def get_school_by_id(db: Session, school_id: int) -> School | None:
    return db.query(School).filter(School.id == school_id).first()


def get_schools(db: Session, offset: int = 0, limit: int = 100) -> list[School]:
    return db.query(School).offset(offset).limit(limit).all()


def get_schools_with_count(
    db: Session, offset: int = 0, limit: int = 100
) -> tuple[list[School], int]:
    total = db.query(School).count()
    items = db.query(School).offset(offset).limit(limit).all()
    return items, total


def update_school(db: Session, school: School, school_data: SchoolUpdate) -> School:
    update_data = school_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(school, field, value)
    db.commit()
    db.refresh(school)
    return school


def delete_school(db: Session, school: School) -> None:
    db.delete(school)
    db.commit()


def get_school_balance(db: Session, school_id: int) -> BalanceResponse:
    """Get balance summary for a school (aggregates all students)."""
    unpaid_statuses = [
        InvoiceStatus.PENDING.value,
        InvoiceStatus.PARTIALLY_PAID.value,
        InvoiceStatus.OVERDUE.value,
    ]

    total_invoiced = (
        db.query(func.coalesce(func.sum(Invoice.amount_in_cents), 0))
        .join(Student, Invoice.student_id == Student.id)
        .filter(Student.school_id == school_id)
        .scalar()
    )

    total_paid = (
        db.query(func.coalesce(func.sum(PaymentAllocation.amount_in_cents), 0))
        .join(Payment, PaymentAllocation.payment_id == Payment.id)
        .join(Invoice, PaymentAllocation.invoice_id == Invoice.id)
        .join(Student, Invoice.student_id == Student.id)
        .filter(
            Student.school_id == school_id,
            Payment.status == PaymentStatus.COMPLETED.value,
        )
        .scalar()
    )

    currency = (
        db.query(Invoice.currency)
        .join(Student, Invoice.student_id == Student.id)
        .filter(Student.school_id == school_id)
        .first()
    )
    currency_value = currency[0] if currency else None

    overdue_invoices = (
        db.query(Invoice)
        .join(Student, Invoice.student_id == Student.id)
        .filter(
            Student.school_id == school_id,
            Invoice.status.in_(unpaid_statuses),
        )
        .order_by(Invoice.amount_in_cents.desc(), Invoice.due_date.asc())
        .limit(10)
        .all()
    )

    recent_payments = (
        db.query(Payment)
        .join(Student, Payment.student_id == Student.id)
        .filter(Student.school_id == school_id)
        .order_by(Payment.created_at.desc())
        .limit(10)
        .all()
    )

    return BalanceResponse(
        total_invoiced_cents=int(total_invoiced),
        total_paid_cents=int(total_paid),
        total_pending_cents=int(total_invoiced) - int(total_paid),
        currency=currency_value,
        invoices=[InvoiceResponse.model_validate(inv) for inv in overdue_invoices],
        payments=[PaymentResponse.model_validate(pay) for pay in recent_payments],
    )
