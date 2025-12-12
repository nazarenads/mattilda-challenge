from sqlalchemy.orm import Session
from app.db.models import Invoice
from app.schemas import InvoiceUpdate


def create_invoice(db: Session, invoice: Invoice) -> Invoice:
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def get_invoice_by_id(db: Session, invoice_id: int) -> Invoice | None:
    return db.query(Invoice).filter(Invoice.id == invoice_id).first()


def get_invoices(db: Session, offset: int = 0, limit: int = 100) -> list[Invoice]:
    return db.query(Invoice).offset(offset).limit(limit).all()


def get_invoices_with_count(
    db: Session, offset: int = 0, limit: int = 100
) -> tuple[list[Invoice], int]:
    total = db.query(Invoice).count()
    items = db.query(Invoice).offset(offset).limit(limit).all()
    return items, total


def update_invoice(db: Session, invoice: Invoice, invoice_data: InvoiceUpdate) -> Invoice:
    update_data = invoice_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)
    db.commit()
    db.refresh(invoice)
    return invoice


def delete_invoice(db: Session, invoice: Invoice) -> None:
    db.delete(invoice)
    db.commit()
