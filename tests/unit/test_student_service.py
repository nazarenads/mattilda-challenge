from datetime import datetime

from app.db.models import Student, InvoiceStatus, PaymentStatus
from app.schemas import StudentUpdate
from app.services import student as student_service


class TestStudentServiceCRUD:
    def test_create_student(self, db_session, db_helpers):
        school = db_helpers.create_school()
        now = datetime.now()
        student = Student(
            identifier="ID-001",
            name="Test Student",
            email="test@example.com",
            school_id=school.id,
            created_at=now,
            updated_at=now,
        )

        result = student_service.create_student(db_session, student)

        assert result.id is not None
        assert result.identifier == "ID-001"
        assert result.name == "Test Student"
        assert result.email == "test@example.com"
        assert result.school_id == school.id

    def test_get_student_by_id(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school, name="Find Me Student")

        result = student_service.get_student_by_id(db_session, student.id)

        assert result is not None
        assert result.id == student.id
        assert result.name == "Find Me Student"

    def test_get_student_by_id_not_found(self, db_session):
        result = student_service.get_student_by_id(db_session, 9999)

        assert result is None

    def test_get_students(self, db_session, db_helpers):
        school = db_helpers.create_school()
        db_helpers.create_student(school, identifier="S1", name="Student 1")
        db_helpers.create_student(school, identifier="S2", name="Student 2", email="s2@example.com")
        db_helpers.create_student(school, identifier="S3", name="Student 3", email="s3@example.com")

        result = student_service.get_students(db_session)

        assert len(result) == 3
        student_names = [s.name for s in result]
        assert "Student 1" in student_names
        assert "Student 2" in student_names
        assert "Student 3" in student_names

    def test_get_students_with_pagination(self, db_session, db_helpers):
        school = db_helpers.create_school()
        for i in range(5):
            db_helpers.create_student(school, identifier=f"S{i}", name=f"Student {i}", email=f"s{i}@example.com")

        result = student_service.get_students(db_session, offset=2, limit=2)

        assert len(result) == 2

    def test_get_students_with_count(self, db_session, db_helpers):
        school = db_helpers.create_school()
        db_helpers.create_student(school, identifier="S1", name="Student A")
        db_helpers.create_student(school, identifier="S2", name="Student B", email="sb@example.com")

        items, total = student_service.get_students_with_count(db_session)

        assert total == 2
        assert len(items) == 2

    def test_get_students_with_count_pagination(self, db_session, db_helpers):
        school = db_helpers.create_school()
        for i in range(5):
            db_helpers.create_student(school, identifier=f"S{i}", name=f"Student {i}", email=f"s{i}@example.com")

        items, total = student_service.get_students_with_count(db_session, offset=0, limit=2)

        assert total == 5
        assert len(items) == 2

    def test_get_students_by_school_with_count(self, db_session, db_helpers):
        school1 = db_helpers.create_school(name="School 1")
        school2 = db_helpers.create_school(name="School 2", tax_id="222")
        db_helpers.create_student(school1, identifier="S1", name="Student 1")
        db_helpers.create_student(school1, identifier="S2", name="Student 2", email="s2@example.com")
        db_helpers.create_student(school2, identifier="S3", name="Student 3", email="s3@example.com")

        items, total = student_service.get_students_by_school_with_count(db_session, school1.id)

        assert total == 2
        assert len(items) == 2
        for student in items:
            assert student.school_id == school1.id

    def test_update_student(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school, name="Original Name")
        update_data = StudentUpdate(name="Updated Name")

        result = student_service.update_student(db_session, student, update_data)

        assert result.name == "Updated Name"
        assert result.id == student.id

    def test_update_student_partial(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school, identifier="ID-001", name="Original", email="orig@example.com")
        update_data = StudentUpdate(email="new@example.com")

        result = student_service.update_student(db_session, student, update_data)

        assert result.identifier == "ID-001"
        assert result.name == "Original"
        assert result.email == "new@example.com"

    def test_delete_student(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        student_id = student.id

        student_service.delete_student(db_session, student)

        assert student_service.get_student_by_id(db_session, student_id) is None


class TestStudentBalanceFunctions:
    def test_get_total_invoiced_for_student_empty(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)

        result = student_service.get_total_invoiced_for_student(db_session, student.id)

        assert result == 0

    def test_get_total_invoiced_for_student(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        db_helpers.create_invoice(student, amount_in_cents=10000)
        db_helpers.create_invoice(student, invoice_number="INV-002", amount_in_cents=5000)

        result = student_service.get_total_invoiced_for_student(db_session, student.id)

        assert result == 15000

    def test_get_total_paid_for_student_empty(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)

        result = student_service.get_total_paid_for_student(db_session, student.id)

        assert result == 0

    def test_get_total_paid_for_student(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, amount_in_cents=10000)
        payment = db_helpers.create_payment(student, amount_in_cents=5000)
        db_helpers.create_allocation(payment, invoice, amount_in_cents=5000)

        result = student_service.get_total_paid_for_student(db_session, student.id)

        assert result == 5000

    def test_get_total_paid_for_student_excludes_pending_payments(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, amount_in_cents=10000)
        pending_payment = db_helpers.create_payment(
            student, amount_in_cents=5000, status=PaymentStatus.PENDING.value
        )
        db_helpers.create_allocation(pending_payment, invoice, amount_in_cents=5000)

        result = student_service.get_total_paid_for_student(db_session, student.id)

        assert result == 0

    def test_get_total_paid_for_student_multiple_allocations(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice1 = db_helpers.create_invoice(student, amount_in_cents=10000)
        invoice2 = db_helpers.create_invoice(student, invoice_number="INV-002", amount_in_cents=5000)
        payment = db_helpers.create_payment(student, amount_in_cents=8000)
        db_helpers.create_allocation(payment, invoice1, amount_in_cents=5000)
        db_helpers.create_allocation(payment, invoice2, amount_in_cents=3000)

        result = student_service.get_total_paid_for_student(db_session, student.id)

        assert result == 8000

    def test_get_currency_for_student_no_invoices(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)

        result = student_service.get_currency_for_student(db_session, student.id)

        assert result is None

    def test_get_currency_for_student(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        db_helpers.create_invoice(student, currency="COP")

        result = student_service.get_currency_for_student(db_session, student.id)

        assert result == "COP"

    def test_get_unpaid_invoices_for_student_empty(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)

        result = student_service.get_unpaid_invoices_for_student(db_session, student.id)

        assert result == []

    def test_get_unpaid_invoices_for_student(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        db_helpers.create_invoice(student, status=InvoiceStatus.PENDING.value, amount_in_cents=5000)
        db_helpers.create_invoice(
            student, invoice_number="INV-002", status=InvoiceStatus.OVERDUE.value, amount_in_cents=10000
        )
        db_helpers.create_invoice(
            student, invoice_number="INV-003", status=InvoiceStatus.PAID.value, amount_in_cents=3000
        )

        result = student_service.get_unpaid_invoices_for_student(db_session, student.id)

        assert len(result) == 2
        assert result[0].amount_in_cents == 10000
        assert result[1].amount_in_cents == 5000

    def test_get_unpaid_invoices_for_student_respects_limit(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        for i in range(15):
            db_helpers.create_invoice(
                student,
                invoice_number=f"INV-{i:03d}",
                status=InvoiceStatus.PENDING.value,
                amount_in_cents=1000 * (i + 1),
            )

        result = student_service.get_unpaid_invoices_for_student(db_session, student.id, limit=5)

        assert len(result) == 5

    def test_get_recent_payments_for_student_empty(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)

        result = student_service.get_recent_payments_for_student(db_session, student.id)

        assert result == []

    def test_get_recent_payments_for_student(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        db_helpers.create_payment(student, amount_in_cents=5000)
        db_helpers.create_payment(student, amount_in_cents=10000)

        result = student_service.get_recent_payments_for_student(db_session, student.id)

        assert len(result) == 2

    def test_get_recent_payments_for_student_respects_limit(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        for i in range(15):
            db_helpers.create_payment(student, amount_in_cents=1000 * (i + 1))

        result = student_service.get_recent_payments_for_student(db_session, student.id, limit=5)

        assert len(result) == 5


class TestStudentBalance:
    def test_get_student_balance_empty(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)

        result = student_service.get_student_balance(db_session, student.id)

        assert result.total_invoiced_cents == 0
        assert result.total_paid_cents == 0
        assert result.total_pending_cents == 0
        assert result.currency is None
        assert result.invoices == []
        assert result.payments == []

    def test_get_student_balance_with_data(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(
            student, amount_in_cents=10000, status=InvoiceStatus.PENDING.value, currency="MXN"
        )
        payment = db_helpers.create_payment(student, amount_in_cents=3000)
        db_helpers.create_allocation(payment, invoice, amount_in_cents=3000)

        result = student_service.get_student_balance(db_session, student.id)

        assert result.total_invoiced_cents == 10000
        assert result.total_paid_cents == 3000
        assert result.total_pending_cents == 7000
        assert result.currency == "MXN"
        assert len(result.invoices) == 1
        assert len(result.payments) == 1

    def test_get_student_balance_excludes_pending_payments(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, amount_in_cents=10000, status=InvoiceStatus.PENDING.value)
        pending_payment = db_helpers.create_payment(
            student, amount_in_cents=10000, status=PaymentStatus.PENDING.value
        )
        db_helpers.create_allocation(pending_payment, invoice, amount_in_cents=10000)

        result = student_service.get_student_balance(db_session, student.id)

        assert result.total_invoiced_cents == 10000
        assert result.total_paid_cents == 0
        assert result.total_pending_cents == 10000
