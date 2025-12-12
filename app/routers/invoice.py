from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import Invoice, User
from app.dependencies import get_db, get_current_active_user, check_school_access
from app.schemas import InvoiceCreate, InvoiceUpdate, InvoiceResponse, PaginatedResponse
from app.services import invoice as invoice_service
from app.services import student as student_service

router = APIRouter(
    prefix="/invoice",
    tags=["invoice"],
)


@router.get("/", response_model=PaginatedResponse[InvoiceResponse])
def list_invoices(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Returns a paginated list of invoices."""
    if current_user.is_admin:
        items, total = invoice_service.get_invoices_with_count(db, offset=offset, limit=limit)
    else:
        items, total = invoice_service.get_invoices_by_school_with_count(
            db, current_user.school_id, offset=offset, limit=limit
        )
    pages = (total + limit - 1) // limit if limit > 0 else 0
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset, pages=pages)


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Returns the invoice details."""
    invoice = invoice_service.get_invoice_by_id(db, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    check_school_access(current_user, invoice.student.school_id)
    return invoice


@router.post("/", response_model=InvoiceResponse, status_code=201)
def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Creates a new invoice."""
    student = student_service.get_student_by_id(db, invoice_data.student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    check_school_access(current_user, student.school_id)

    now = datetime.now()
    invoice = Invoice(
        invoice_number=invoice_data.invoice_number,
        amount_in_cents=invoice_data.amount_in_cents,
        currency=invoice_data.currency,
        status=invoice_data.status.value,
        issue_date=invoice_data.issue_date,
        due_date=invoice_data.due_date,
        description=invoice_data.description,
        student_id=invoice_data.student_id,
        created_at=now,
        updated_at=now,
    )
    return invoice_service.create_invoice(db, invoice)


@router.put("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(
    invoice_id: int,
    invoice_data: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Updates an existing invoice."""
    invoice = invoice_service.get_invoice_by_id(db, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    check_school_access(current_user, invoice.student.school_id)

    if invoice_data.student_id is not None:
        student = student_service.get_student_by_id(db, invoice_data.student_id)
        if student is None:
            raise HTTPException(status_code=404, detail="Student not found")
        check_school_access(current_user, student.school_id)

    invoice.updated_at = datetime.now()
    return invoice_service.update_invoice(db, invoice, invoice_data)


@router.delete("/{invoice_id}", status_code=204)
def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Deletes an invoice."""
    invoice = invoice_service.get_invoice_by_id(db, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    check_school_access(current_user, invoice.student.school_id)
    invoice_service.delete_invoice(db, invoice)
