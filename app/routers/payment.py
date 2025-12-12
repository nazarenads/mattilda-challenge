from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas import PaymentCreate, PaymentUpdate, PaymentResponse, PaginatedResponse
from app.services import payment as payment_service
from app.services import student as student_service
from app.db.models import Payment

router = APIRouter(
    prefix="/payment",
    tags=["payment"],
)


@router.get("/", response_model=PaginatedResponse[PaymentResponse])
def list_payments(limit: int = 100, offset: int = 0, db: Session = Depends(get_db)):
    """Returns a paginated list of payments."""
    items, total = payment_service.get_payments_with_count(db, offset=offset, limit=limit)
    pages = (total + limit - 1) // limit if limit > 0 else 0
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset, pages=pages)


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    """Returns the payment details."""
    payment = payment_service.get_payment_by_id(db, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.post("/", response_model=PaymentResponse, status_code=201)
def create_payment(payment_data: PaymentCreate, db: Session = Depends(get_db)):
    """Creates a new payment."""
    student = student_service.get_student_by_id(db, payment_data.student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    now = datetime.now()
    payment = Payment(
        amount_in_cents=payment_data.amount_in_cents,
        status=payment_data.status.value,
        payment_method=payment_data.payment_method.value,
        student_id=payment_data.student_id,
        created_at=now,
        updated_at=now,
    )
    return payment_service.create_payment(db, payment)


@router.put("/{payment_id}", response_model=PaymentResponse)
def update_payment(
    payment_id: int, payment_data: PaymentUpdate, db: Session = Depends(get_db)
):
    """Updates an existing payment."""
    payment = payment_service.get_payment_by_id(db, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment_data.student_id is not None:
        student = student_service.get_student_by_id(db, payment_data.student_id)
        if student is None:
            raise HTTPException(status_code=404, detail="Student not found")

    payment.updated_at = datetime.now()
    return payment_service.update_payment(db, payment, payment_data)


@router.delete("/{payment_id}", status_code=204)
def delete_payment(payment_id: int, db: Session = Depends(get_db)):
    """Deletes a payment."""
    payment = payment_service.get_payment_by_id(db, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    payment_service.delete_payment(db, payment)
