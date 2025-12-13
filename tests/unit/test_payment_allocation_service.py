from datetime import datetime

from app.db.models import PaymentAllocation, InvoiceStatus, PaymentStatus
from app.schemas import PaymentAllocationUpdate
from app.services import payment_allocation as allocation_service


class TestPaymentAllocationServiceCRUD:
    def test_create_allocation(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, amount_in_cents=10000)
        payment = db_helpers.create_payment(student, amount_in_cents=10000)
        now = datetime.now()
        allocation = PaymentAllocation(
            payment_id=payment.id,
            invoice_id=invoice.id,
            amount_in_cents=5000,
            created_at=now,
        )

        result = allocation_service.create_allocation(db_session, allocation)

        assert result.id is not None
        assert result.payment_id == payment.id
        assert result.invoice_id == invoice.id
        assert result.amount_in_cents == 5000

    def test_get_allocation_by_id(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student)
        payment = db_helpers.create_payment(student)
        allocation = db_helpers.create_allocation(payment, invoice, amount_in_cents=3000)

        result = allocation_service.get_allocation_by_id(db_session, allocation.id)

        assert result is not None
        assert result.id == allocation.id
        assert result.amount_in_cents == 3000

    def test_get_allocation_by_id_not_found(self, db_session):
        result = allocation_service.get_allocation_by_id(db_session, 9999)

        assert result is None

    def test_get_allocations(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student)
        payment = db_helpers.create_payment(student, amount_in_cents=15000)
        db_helpers.create_allocation(payment, invoice, amount_in_cents=1000)
        db_helpers.create_allocation(payment, invoice, amount_in_cents=2000)
        db_helpers.create_allocation(payment, invoice, amount_in_cents=3000)

        result = allocation_service.get_allocations(db_session)

        assert len(result) == 3
        amounts = [a.amount_in_cents for a in result]
        assert 1000 in amounts
        assert 2000 in amounts
        assert 3000 in amounts

    def test_get_allocations_with_pagination(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student)
        payment = db_helpers.create_payment(student, amount_in_cents=50000)
        for i in range(5):
            db_helpers.create_allocation(payment, invoice, amount_in_cents=1000 * (i + 1))

        result = allocation_service.get_allocations(db_session, offset=2, limit=2)

        assert len(result) == 2

    def test_get_allocations_with_count(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student)
        payment = db_helpers.create_payment(student, amount_in_cents=10000)
        db_helpers.create_allocation(payment, invoice, amount_in_cents=1000)
        db_helpers.create_allocation(payment, invoice, amount_in_cents=2000)

        items, total = allocation_service.get_allocations_with_count(db_session)

        assert total == 2
        assert len(items) == 2

    def test_get_allocations_with_count_pagination(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student)
        payment = db_helpers.create_payment(student, amount_in_cents=50000)
        for i in range(5):
            db_helpers.create_allocation(payment, invoice, amount_in_cents=1000 * (i + 1))

        items, total = allocation_service.get_allocations_with_count(db_session, offset=0, limit=2)

        assert total == 5
        assert len(items) == 2

    def test_get_allocations_by_school_with_count(self, db_session, db_helpers):
        school1 = db_helpers.create_school(name="School 1")
        school2 = db_helpers.create_school(name="School 2", tax_id="222")
        student1 = db_helpers.create_student(school1, identifier="S1")
        student2 = db_helpers.create_student(school2, identifier="S2", email="s2@example.com")
        invoice1 = db_helpers.create_invoice(student1, invoice_number="INV-001")
        invoice2 = db_helpers.create_invoice(student2, invoice_number="INV-002")
        payment1 = db_helpers.create_payment(student1, amount_in_cents=5000)
        payment2 = db_helpers.create_payment(student2, amount_in_cents=5000)
        db_helpers.create_allocation(payment1, invoice1, amount_in_cents=1000)
        db_helpers.create_allocation(payment1, invoice1, amount_in_cents=2000)
        db_helpers.create_allocation(payment2, invoice2, amount_in_cents=3000)

        items, total = allocation_service.get_allocations_by_school_with_count(db_session, school1.id)

        assert total == 2
        assert len(items) == 2

    def test_update_allocation(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student)
        payment = db_helpers.create_payment(student, amount_in_cents=10000)
        allocation = db_helpers.create_allocation(payment, invoice, amount_in_cents=3000)
        update_data = PaymentAllocationUpdate(amount_in_cents=5000)

        result = allocation_service.update_allocation(db_session, allocation, update_data)

        assert result.amount_in_cents == 5000
        assert result.id == allocation.id

    def test_delete_allocation(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student)
        payment = db_helpers.create_payment(student)
        allocation = db_helpers.create_allocation(payment, invoice)
        allocation_id = allocation.id

        allocation_service.delete_allocation(db_session, allocation)

        assert allocation_service.get_allocation_by_id(db_session, allocation_id) is None


class TestInvoicePaidAmount:
    def test_get_invoice_paid_amount_no_allocations(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, amount_in_cents=10000)

        result = allocation_service.get_invoice_paid_amount(db_session, invoice.id)

        assert result == 0

    def test_get_invoice_paid_amount_single_allocation(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, amount_in_cents=10000)
        payment = db_helpers.create_payment(student, amount_in_cents=5000)
        db_helpers.create_allocation(payment, invoice, amount_in_cents=5000)

        result = allocation_service.get_invoice_paid_amount(db_session, invoice.id)

        assert result == 5000

    def test_get_invoice_paid_amount_multiple_allocations(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, amount_in_cents=10000)
        payment1 = db_helpers.create_payment(student, amount_in_cents=3000)
        payment2 = db_helpers.create_payment(student, amount_in_cents=4000)
        db_helpers.create_allocation(payment1, invoice, amount_in_cents=3000)
        db_helpers.create_allocation(payment2, invoice, amount_in_cents=4000)

        result = allocation_service.get_invoice_paid_amount(db_session, invoice.id)

        assert result == 7000

    def test_get_invoice_paid_amount_excludes_pending_payments(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, amount_in_cents=10000)
        completed_payment = db_helpers.create_payment(
            student, amount_in_cents=3000, status=PaymentStatus.COMPLETED.value
        )
        pending_payment = db_helpers.create_payment(
            student, amount_in_cents=5000, status=PaymentStatus.PENDING.value
        )
        db_helpers.create_allocation(completed_payment, invoice, amount_in_cents=3000)
        db_helpers.create_allocation(pending_payment, invoice, amount_in_cents=5000)

        result = allocation_service.get_invoice_paid_amount(db_session, invoice.id)

        assert result == 3000

    def test_get_invoice_paid_amount_excludes_failed_payments(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, amount_in_cents=10000)
        completed_payment = db_helpers.create_payment(
            student, amount_in_cents=3000, status=PaymentStatus.COMPLETED.value
        )
        failed_payment = db_helpers.create_payment(
            student, amount_in_cents=5000, status=PaymentStatus.FAILED.value
        )
        db_helpers.create_allocation(completed_payment, invoice, amount_in_cents=3000)
        db_helpers.create_allocation(failed_payment, invoice, amount_in_cents=5000)

        result = allocation_service.get_invoice_paid_amount(db_session, invoice.id)

        assert result == 3000


class TestUpdateInvoiceStatusFromPayments:
    def test_update_invoice_status_no_payments(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, amount_in_cents=10000, status=InvoiceStatus.PENDING.value)

        result = allocation_service.update_invoice_status_from_payments(db_session, invoice)

        assert result.status == InvoiceStatus.PENDING.value

    def test_update_invoice_status_partial_payment(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, amount_in_cents=10000, status=InvoiceStatus.PENDING.value)
        payment = db_helpers.create_payment(student, amount_in_cents=5000)
        db_helpers.create_allocation(payment, invoice, amount_in_cents=5000)

        result = allocation_service.update_invoice_status_from_payments(db_session, invoice)

        assert result.status == InvoiceStatus.PARTIALLY_PAID.value

    def test_update_invoice_status_full_payment(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, amount_in_cents=10000, status=InvoiceStatus.PENDING.value)
        payment = db_helpers.create_payment(student, amount_in_cents=10000)
        db_helpers.create_allocation(payment, invoice, amount_in_cents=10000)

        result = allocation_service.update_invoice_status_from_payments(db_session, invoice)

        assert result.status == InvoiceStatus.PAID.value

    def test_update_invoice_status_overpayment(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, amount_in_cents=10000, status=InvoiceStatus.PENDING.value)
        payment = db_helpers.create_payment(student, amount_in_cents=15000)
        db_helpers.create_allocation(payment, invoice, amount_in_cents=15000)

        result = allocation_service.update_invoice_status_from_payments(db_session, invoice)

        assert result.status == InvoiceStatus.PAID.value

    def test_update_invoice_status_multiple_payments(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, amount_in_cents=10000, status=InvoiceStatus.PENDING.value)
        payment1 = db_helpers.create_payment(student, amount_in_cents=3000)
        payment2 = db_helpers.create_payment(student, amount_in_cents=7000)
        db_helpers.create_allocation(payment1, invoice, amount_in_cents=3000)
        db_helpers.create_allocation(payment2, invoice, amount_in_cents=7000)

        result = allocation_service.update_invoice_status_from_payments(db_session, invoice)

        assert result.status == InvoiceStatus.PAID.value

    def test_update_invoice_status_ignores_pending_payments(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, amount_in_cents=10000, status=InvoiceStatus.PENDING.value)
        pending_payment = db_helpers.create_payment(
            student, amount_in_cents=10000, status=PaymentStatus.PENDING.value
        )
        db_helpers.create_allocation(pending_payment, invoice, amount_in_cents=10000)

        result = allocation_service.update_invoice_status_from_payments(db_session, invoice)

        assert result.status == InvoiceStatus.PENDING.value

    def test_update_invoice_status_from_overdue_to_partially_paid(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, amount_in_cents=10000, status=InvoiceStatus.OVERDUE.value)
        payment = db_helpers.create_payment(student, amount_in_cents=3000)
        db_helpers.create_allocation(payment, invoice, amount_in_cents=3000)

        result = allocation_service.update_invoice_status_from_payments(db_session, invoice)

        assert result.status == InvoiceStatus.PARTIALLY_PAID.value

    def test_update_invoice_status_from_overdue_to_paid(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, amount_in_cents=10000, status=InvoiceStatus.OVERDUE.value)
        payment = db_helpers.create_payment(student, amount_in_cents=10000)
        db_helpers.create_allocation(payment, invoice, amount_in_cents=10000)

        result = allocation_service.update_invoice_status_from_payments(db_session, invoice)

        assert result.status == InvoiceStatus.PAID.value
