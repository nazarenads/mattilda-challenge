from datetime import datetime

from app.db.models import Invoice, InvoiceStatus
from app.schemas import InvoiceUpdate
from app.services import invoice as invoice_service


class TestInvoiceServiceCRUD:
    def test_create_invoice(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        now = datetime.now()
        invoice = Invoice(
            invoice_number="INV-001",
            amount_in_cents=10000,
            currency="USD",
            status=InvoiceStatus.PENDING.value,
            issue_date=now,
            due_date=now,
            student_id=student.id,
            created_at=now,
            updated_at=now,
        )

        result = invoice_service.create_invoice(db_session, invoice)

        assert result.id is not None
        assert result.invoice_number == "INV-001"
        assert result.amount_in_cents == 10000
        assert result.currency == "USD"
        assert result.status == InvoiceStatus.PENDING.value
        assert result.student_id == student.id

    def test_get_invoice_by_id(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, invoice_number="FIND-ME")

        result = invoice_service.get_invoice_by_id(db_session, invoice.id)

        assert result is not None
        assert result.id == invoice.id
        assert result.invoice_number == "FIND-ME"

    def test_get_invoice_by_id_not_found(self, db_session):
        result = invoice_service.get_invoice_by_id(db_session, 9999)

        assert result is None

    def test_get_invoices(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        db_helpers.create_invoice(student, invoice_number="INV-001")
        db_helpers.create_invoice(student, invoice_number="INV-002")
        db_helpers.create_invoice(student, invoice_number="INV-003")

        result = invoice_service.get_invoices(db_session)

        assert len(result) == 3
        invoice_numbers = [i.invoice_number for i in result]
        assert "INV-001" in invoice_numbers
        assert "INV-002" in invoice_numbers
        assert "INV-003" in invoice_numbers

    def test_get_invoices_with_pagination(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        for i in range(5):
            db_helpers.create_invoice(student, invoice_number=f"INV-{i:03d}")

        result = invoice_service.get_invoices(db_session, offset=2, limit=2)

        assert len(result) == 2

    def test_get_invoices_with_count(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        db_helpers.create_invoice(student, invoice_number="INV-A")
        db_helpers.create_invoice(student, invoice_number="INV-B")

        items, total = invoice_service.get_invoices_with_count(db_session)

        assert total == 2
        assert len(items) == 2

    def test_get_invoices_with_count_pagination(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        for i in range(5):
            db_helpers.create_invoice(student, invoice_number=f"INV-{i:03d}")

        items, total = invoice_service.get_invoices_with_count(db_session, offset=0, limit=2)

        assert total == 5
        assert len(items) == 2

    def test_get_invoices_by_school_with_count(self, db_session, db_helpers):
        school1 = db_helpers.create_school(name="School 1")
        school2 = db_helpers.create_school(name="School 2", tax_id="222")
        student1 = db_helpers.create_student(school1, identifier="S1")
        student2 = db_helpers.create_student(school2, identifier="S2", email="s2@example.com")
        db_helpers.create_invoice(student1, invoice_number="INV-001")
        db_helpers.create_invoice(student1, invoice_number="INV-002")
        db_helpers.create_invoice(student2, invoice_number="INV-003")

        items, total = invoice_service.get_invoices_by_school_with_count(db_session, school1.id)

        assert total == 2
        assert len(items) == 2
        for invoice in items:
            assert invoice.student.school_id == school1.id

    def test_update_invoice(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, amount_in_cents=10000)
        update_data = InvoiceUpdate(amount_in_cents=15000)

        result = invoice_service.update_invoice(db_session, invoice, update_data)

        assert result.amount_in_cents == 15000
        assert result.id == invoice.id

    def test_update_invoice_partial(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(
            student,
            invoice_number="INV-001",
            amount_in_cents=10000,
            status=InvoiceStatus.PENDING.value,
        )
        update_data = InvoiceUpdate(status=InvoiceStatus.OVERDUE.value)

        result = invoice_service.update_invoice(db_session, invoice, update_data)

        assert result.invoice_number == "INV-001"
        assert result.amount_in_cents == 10000
        assert result.status == InvoiceStatus.OVERDUE.value

    def test_update_invoice_description(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, description="Original description")
        update_data = InvoiceUpdate(description="Updated description")

        result = invoice_service.update_invoice(db_session, invoice, update_data)

        assert result.description == "Updated description"

    def test_delete_invoice(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student)
        invoice_id = invoice.id

        invoice_service.delete_invoice(db_session, invoice)

        assert invoice_service.get_invoice_by_id(db_session, invoice_id) is None


class TestInvoiceServiceFiltering:
    def test_get_invoices_by_school_excludes_other_schools(self, db_session, db_helpers):
        school1 = db_helpers.create_school(name="School 1")
        school2 = db_helpers.create_school(name="School 2", tax_id="222")
        student1 = db_helpers.create_student(school1, identifier="S1")
        student2 = db_helpers.create_student(school2, identifier="S2", email="s2@example.com")
        db_helpers.create_invoice(student1, invoice_number="INV-SCHOOL1")
        db_helpers.create_invoice(student2, invoice_number="INV-SCHOOL2")

        items, total = invoice_service.get_invoices_by_school_with_count(db_session, school1.id)

        assert total == 1
        assert items[0].invoice_number == "INV-SCHOOL1"

    def test_get_invoices_by_school_with_pagination(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        for i in range(10):
            db_helpers.create_invoice(student, invoice_number=f"INV-{i:03d}")

        items, total = invoice_service.get_invoices_by_school_with_count(db_session, school.id, limit=3, offset=0)

        assert total == 10
        assert len(items) == 3
