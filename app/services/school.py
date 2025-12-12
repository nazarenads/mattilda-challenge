from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import School, Student, Invoice, Payment, PaymentAllocation, PaymentStatus
from app.schemas import SchoolUpdate, BalanceResponse, InvoiceResponse, PaymentResponse
from app.constants import UNPAID_INVOICE_STATUSES


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


def get_total_invoiced_for_school(db: Session, school_id: int) -> int:
    result = (
        db.query(func.coalesce(func.sum(Invoice.amount_in_cents), 0))
        .join(Student, Invoice.student_id == Student.id)
        .filter(Student.school_id == school_id)
        .scalar()
    )
    return int(result)


def get_total_paid_for_school(db: Session, school_id: int) -> int:
    result = (
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
    return int(result)


def get_currency_for_school(db: Session, school_id: int) -> str | None:
    result = (
        db.query(Invoice.currency)
        .join(Student, Invoice.student_id == Student.id)
        .filter(Student.school_id == school_id)
        .first()
    )
    return result[0] if result else None


def get_unpaid_invoices_for_school(db: Session, school_id: int, limit: int = 10) -> list[Invoice]:
    return (
        db.query(Invoice)
        .join(Student, Invoice.student_id == Student.id)
        .filter(
            Student.school_id == school_id,
            Invoice.status.in_(UNPAID_INVOICE_STATUSES),
        )
        .order_by(Invoice.amount_in_cents.desc(), Invoice.due_date.asc())
        .limit(limit)
        .all()
    )


def get_recent_payments_for_school(db: Session, school_id: int, limit: int = 10) -> list[Payment]:
    return (
        db.query(Payment)
        .join(Student, Payment.student_id == Student.id)
        .filter(Student.school_id == school_id)
        .order_by(Payment.created_at.desc())
        .limit(limit)
        .all()
    )


def get_school_balance(db: Session, school_id: int) -> BalanceResponse:
    total_invoiced = get_total_invoiced_for_school(db, school_id)
    total_paid = get_total_paid_for_school(db, school_id)
    currency = get_currency_for_school(db, school_id)
    invoices = get_unpaid_invoices_for_school(db, school_id)
    payments = get_recent_payments_for_school(db, school_id)

    return BalanceResponse(
        total_invoiced_cents=total_invoiced,
        total_paid_cents=total_paid,
        total_pending_cents=total_invoiced - total_paid,
        currency=currency,
        invoices=[InvoiceResponse.model_validate(inv) for inv in invoices],
        payments=[PaymentResponse.model_validate(pay) for pay in payments],
    )
