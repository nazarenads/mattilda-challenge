from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import Payment, User
from app.dependencies import get_db, get_current_active_user
from app.schemas import PaymentCreate, PaymentUpdate, PaymentResponse, PaginatedResponse
from app.services import payment as payment_service
from app.services import student as student_service
from app.validators.payment import validate_payment_update, validate_payment_delete

router = APIRouter(
    prefix="/payment",
    tags=["payment"],
)


@router.get("/", response_model=PaginatedResponse[PaymentResponse])
def list_payments(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Returns a paginated list of payments."""
    if current_user.is_admin:
        items, total = payment_service.get_payments_with_count(db, offset=offset, limit=limit)
    else:
        items, total = payment_service.get_payments_by_school_with_count(
            db, current_user.school_id, offset=offset, limit=limit
        )
    pages = (total + limit - 1) // limit if limit > 0 else 0
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset, pages=pages)


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Returns the payment details."""
    payment = payment_service.get_payment_by_id_for_user(db, payment_id, current_user)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.post("/", response_model=PaymentResponse, status_code=201)
def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Creates a new payment."""
    student = student_service.get_student_by_id_for_user(db, payment_data.student_id, current_user)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    now = datetime.now()
    payment = Payment(
        amount_in_cents=payment_data.amount_in_cents,
        currency=payment_data.currency,
        status=payment_data.status.value,
        payment_method=payment_data.payment_method.value,
        student_id=payment_data.student_id,
        created_at=now,
        updated_at=now,
    )
    return payment_service.create_payment(db, payment)


@router.put("/{payment_id}", response_model=PaymentResponse)
def update_payment(
    payment_id: int,
    payment_data: PaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Updates an existing payment."""
    payment = payment_service.get_payment_by_id_for_user(db, payment_id, current_user)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment_data.student_id is not None:
        student = student_service.get_student_by_id_for_user(db, payment_data.student_id, current_user)
        if student is None:
            raise HTTPException(status_code=404, detail="Student not found")

    # Validate payment update rules (cannot modify allocated payments, etc.)
    validate_payment_update(
        db,
        payment,
        new_status=payment_data.status.value if payment_data.status else None,
        new_amount=payment_data.amount_in_cents,
    )

    payment.updated_at = datetime.now()
    return payment_service.update_payment(db, payment, payment_data)


@router.delete("/{payment_id}", status_code=204)
def delete_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Deletes a payment."""
    payment = payment_service.get_payment_by_id_for_user(db, payment_id, current_user)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Validate payment can be deleted (no allocations)
    validate_payment_delete(db, payment)

    payment_service.delete_payment(db, payment)
