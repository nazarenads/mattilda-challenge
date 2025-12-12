from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import Student, Invoice, Payment, PaymentAllocation, PaymentStatus
from app.schemas import StudentUpdate, BalanceResponse, InvoiceResponse, PaymentResponse
from app.constants import UNPAID_INVOICE_STATUSES


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


def get_students_by_school_with_count(
    db: Session, school_id: int, offset: int = 0, limit: int = 100
) -> tuple[list[Student], int]:
    query = db.query(Student).filter(Student.school_id == school_id)
    total = query.count()
    items = query.offset(offset).limit(limit).all()
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


def get_total_invoiced_for_student(db: Session, student_id: int) -> int:
    result = (
        db.query(func.coalesce(func.sum(Invoice.amount_in_cents), 0))
        .filter(Invoice.student_id == student_id)
        .scalar()
    )
    return int(result)


def get_total_paid_for_student(db: Session, student_id: int) -> int:
    result = (
        db.query(func.coalesce(func.sum(PaymentAllocation.amount_in_cents), 0))
        .join(Payment, PaymentAllocation.payment_id == Payment.id)
        .join(Invoice, PaymentAllocation.invoice_id == Invoice.id)
        .filter(
            Invoice.student_id == student_id,
            Payment.status == PaymentStatus.COMPLETED.value,
        )
        .scalar()
    )
    return int(result)


def get_currency_for_student(db: Session, student_id: int) -> str | None:
    result = (
        db.query(Invoice.currency)
        .filter(Invoice.student_id == student_id)
        .first()
    )
    return result[0] if result else None


def get_unpaid_invoices_for_student(db: Session, student_id: int, limit: int = 10) -> list[Invoice]:
    return (
        db.query(Invoice)
        .filter(
            Invoice.student_id == student_id,
            Invoice.status.in_(UNPAID_INVOICE_STATUSES),
        )
        .order_by(Invoice.amount_in_cents.desc(), Invoice.due_date.asc())
        .limit(limit)
        .all()
    )


def get_recent_payments_for_student(db: Session, student_id: int, limit: int = 10) -> list[Payment]:
    return (
        db.query(Payment)
        .filter(Payment.student_id == student_id)
        .order_by(Payment.created_at.desc())
        .limit(limit)
        .all()
    )


def get_student_balance(db: Session, student_id: int) -> BalanceResponse:
    total_invoiced = get_total_invoiced_for_student(db, student_id)
    total_paid = get_total_paid_for_student(db, student_id)
    currency = get_currency_for_student(db, student_id)
    invoices = get_unpaid_invoices_for_student(db, student_id)
    payments = get_recent_payments_for_student(db, student_id)

    return BalanceResponse(
        total_invoiced_cents=total_invoiced,
        total_paid_cents=total_paid,
        total_pending_cents=total_invoiced - total_paid,
        currency=currency,
        invoices=[InvoiceResponse.model_validate(inv) for inv in invoices],
        payments=[PaymentResponse.model_validate(pay) for pay in payments],
    )
