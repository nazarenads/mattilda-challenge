from app.db.models import InvoiceStatus

UNPAID_INVOICE_STATUSES = [
    InvoiceStatus.PENDING.value,
    InvoiceStatus.PARTIALLY_PAID.value,
    InvoiceStatus.OVERDUE.value,
]
