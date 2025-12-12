from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import Student, Invoice, Payment, PaymentAllocation, InvoiceStatus, PaymentStatus
from app.schemas import StudentUpdate, BalanceResponse, InvoiceResponse, PaymentResponse


def create_student(db: Session, student: Student) -> Student:
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def get_student_by_id(db: Session, student_id: int) -> Student | None:
    return db.query(Student).filter(Student.id == student_id).first()


def get_students(db: Session, offset: int = 0, limit: int = 100) -> list[Student]:
    return db.query(Student).offset(offset).limit(limit).all()


def get_students_with_count(
    db: Session, offset: int = 0, limit: int = 100
) -> tuple[list[Student], int]:
    total = db.query(Student).count()
    items = db.query(Student).offset(offset).limit(limit).all()
    return items, total


def update_student(db: Session, student: Student, student_data: StudentUpdate) -> Student:
    update_data = student_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


def delete_student(db: Session, student: Student) -> None:
    db.delete(student)
    db.commit()


def get_student_balance(db: Session, student_id: int) -> BalanceResponse:
    """Get balance summary for a student."""
    unpaid_statuses = [
        InvoiceStatus.PENDING.value,
        InvoiceStatus.PARTIALLY_PAID.value,
        InvoiceStatus.OVERDUE.value,
    ]

    total_invoiced = (
        db.query(func.coalesce(func.sum(Invoice.amount_in_cents), 0))
        .filter(Invoice.student_id == student_id)
        .scalar()
    )

    total_paid = (
        db.query(func.coalesce(func.sum(PaymentAllocation.amount_in_cents), 0))
        .join(Payment, PaymentAllocation.payment_id == Payment.id)
        .join(Invoice, PaymentAllocation.invoice_id == Invoice.id)
        .filter(
            Invoice.student_id == student_id,
            Payment.status == PaymentStatus.COMPLETED.value,
        )
        .scalar()
    )

    currency = (
        db.query(Invoice.currency)
        .filter(Invoice.student_id == student_id)
        .first()
    )
    currency_value = currency[0] if currency else None

    overdue_invoices = (
        db.query(Invoice)
        .filter(
            Invoice.student_id == student_id,
            Invoice.status.in_(unpaid_statuses),
        )
        .order_by(Invoice.amount_in_cents.desc(), Invoice.due_date.asc())
        .limit(10)
        .all()
    )

    recent_payments = (
        db.query(Payment)
        .filter(Payment.student_id == student_id)
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
