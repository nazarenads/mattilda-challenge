from sqlalchemy.orm import Session
from app.db.models import Payment, Student, User
from app.schemas import PaymentUpdate


def create_payment(db: Session, payment: Payment) -> Payment:
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def get_payment_by_id(db: Session, payment_id: int) -> Payment | None:
    return db.query(Payment).filter(Payment.id == payment_id).first()


def get_payment_by_id_for_user(db: Session, payment_id: int, user: User) -> Payment | None:
    """Get payment by ID, filtered by user's school access."""
    query = db.query(Payment).filter(Payment.id == payment_id)
    if not user.is_admin:
        query = query.join(Student).filter(Student.school_id == user.school_id)
    return query.first()


def get_payments(db: Session, offset: int = 0, limit: int = 100) -> list[Payment]:
    return db.query(Payment).offset(offset).limit(limit).all()


def get_payments_with_count(
    db: Session, offset: int = 0, limit: int = 100
) -> tuple[list[Payment], int]:
    total = db.query(Payment).count()
    items = db.query(Payment).offset(offset).limit(limit).all()
    return items, total


def get_payments_by_school_with_count(
    db: Session, school_id: int, offset: int = 0, limit: int = 100
) -> tuple[list[Payment], int]:
    query = (
        db.query(Payment)
        .join(Student, Payment.student_id == Student.id)
        .filter(Student.school_id == school_id)
    )
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    return items, total


def update_payment(db: Session, payment: Payment, payment_data: PaymentUpdate) -> Payment:
    update_data = payment_data.model_dump(exclude_unset=True, mode="json")
    for field, value in update_data.items():
        setattr(payment, field, value)
    db.commit()
    db.refresh(payment)
    return payment


def delete_payment(db: Session, payment: Payment) -> None:
    db.delete(payment)
    db.commit()
