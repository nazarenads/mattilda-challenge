from datetime import datetime

from app.db.models import School, InvoiceStatus, PaymentStatus
from app.schemas import SchoolUpdate
from app.services import school as school_service


class TestSchoolServiceCRUD:
    def test_create_school(self, db_session):
        now = datetime.now()
        school = School(
            name="Test School",
            country="US",
            tax_id="123456789",
            created_at=now,
            updated_at=now,
        )

        result = school_service.create_school(db_session, school)

        assert result.id is not None
        assert result.name == "Test School"
        assert result.country == "US"
        assert result.tax_id == "123456789"

    def test_get_school_by_id(self, db_session, db_helpers):
        school = db_helpers.create_school(name="Find Me School")

        result = school_service.get_school_by_id(db_session, school.id)

        assert result is not None
        assert result.id == school.id
        assert result.name == "Find Me School"

    def test_get_school_by_id_not_found(self, db_session):
        result = school_service.get_school_by_id(db_session, 9999)

        assert result is None

    def test_get_schools(self, db_session, db_helpers):
        db_helpers.create_school(name="School 1")
        db_helpers.create_school(name="School 2", tax_id="987654321")
        db_helpers.create_school(name="School 3", tax_id="111222333")

        result = school_service.get_schools(db_session)

        assert len(result) == 3
        school_names = [s.name for s in result]
        assert "School 1" in school_names
        assert "School 2" in school_names
        assert "School 3" in school_names

    def test_get_schools_with_pagination(self, db_session, db_helpers):
        for i in range(5):
            db_helpers.create_school(name=f"School {i}", tax_id=f"tax{i}")

        result = school_service.get_schools(db_session, offset=2, limit=2)

        assert len(result) == 2

    def test_get_schools_with_count(self, db_session, db_helpers):
        db_helpers.create_school(name="School A")
        db_helpers.create_school(name="School B", tax_id="222333444")

        items, total = school_service.get_schools_with_count(db_session)

        assert total == 2
        assert len(items) == 2

    def test_get_schools_with_count_pagination(self, db_session, db_helpers):
        for i in range(5):
            db_helpers.create_school(name=f"School {i}", tax_id=f"tax{i}")

        items, total = school_service.get_schools_with_count(db_session, offset=0, limit=2)

        assert total == 5
        assert len(items) == 2

    def test_update_school(self, db_session, db_helpers):
        school = db_helpers.create_school(name="Original Name")
        update_data = SchoolUpdate(name="Updated Name")

        result = school_service.update_school(db_session, school, update_data)

        assert result.name == "Updated Name"
        assert result.id == school.id

    def test_update_school_partial(self, db_session, db_helpers):
        school = db_helpers.create_school(name="Original", country="US", tax_id="111")
        update_data = SchoolUpdate(country="MX")

        result = school_service.update_school(db_session, school, update_data)

        assert result.name == "Original"
        assert result.country == "MX"
        assert result.tax_id == "111"

    def test_delete_school(self, db_session, db_helpers):
        school = db_helpers.create_school()
        school_id = school.id

        school_service.delete_school(db_session, school)

        assert school_service.get_school_by_id(db_session, school_id) is None


class TestSchoolBalanceFunctions:
    def test_get_total_invoiced_for_school_empty(self, db_session, db_helpers):
        school = db_helpers.create_school()

        result = school_service.get_total_invoiced_for_school(db_session, school.id)

        assert result == 0

    def test_get_total_invoiced_for_school(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        db_helpers.create_invoice(student, amount_in_cents=10000)
        db_helpers.create_invoice(student, invoice_number="INV-002", amount_in_cents=5000)

        result = school_service.get_total_invoiced_for_school(db_session, school.id)

        assert result == 15000

    def test_get_total_invoiced_for_school_multiple_students(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student1 = db_helpers.create_student(school, identifier="S1")
        student2 = db_helpers.create_student(school, identifier="S2", email="s2@example.com")
        db_helpers.create_invoice(student1, amount_in_cents=10000)
        db_helpers.create_invoice(student2, invoice_number="INV-002", amount_in_cents=5000)

        result = school_service.get_total_invoiced_for_school(db_session, school.id)

        assert result == 15000

    def test_get_total_paid_for_school_empty(self, db_session, db_helpers):
        school = db_helpers.create_school()

        result = school_service.get_total_paid_for_school(db_session, school.id)

        assert result == 0

    def test_get_total_paid_for_school(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, amount_in_cents=10000)
        payment = db_helpers.create_payment(student, amount_in_cents=5000)
        db_helpers.create_allocation(payment, invoice, amount_in_cents=5000)

        result = school_service.get_total_paid_for_school(db_session, school.id)

        assert result == 5000

    def test_get_total_paid_for_school_excludes_pending_payments(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, amount_in_cents=10000)
        pending_payment = db_helpers.create_payment(
            student, amount_in_cents=5000, status=PaymentStatus.PENDING.value
        )
        db_helpers.create_allocation(pending_payment, invoice, amount_in_cents=5000)

        result = school_service.get_total_paid_for_school(db_session, school.id)

        assert result == 0

    def test_get_total_paid_for_school_multiple_allocations(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice1 = db_helpers.create_invoice(student, amount_in_cents=10000)
        invoice2 = db_helpers.create_invoice(student, invoice_number="INV-002", amount_in_cents=5000)
        payment = db_helpers.create_payment(student, amount_in_cents=8000)
        db_helpers.create_allocation(payment, invoice1, amount_in_cents=5000)
        db_helpers.create_allocation(payment, invoice2, amount_in_cents=3000)

        result = school_service.get_total_paid_for_school(db_session, school.id)

        assert result == 8000

    def test_get_currency_for_school_no_invoices(self, db_session, db_helpers):
        school = db_helpers.create_school()

        result = school_service.get_currency_for_school(db_session, school.id)

        assert result is None

    def test_get_currency_for_school(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        db_helpers.create_invoice(student, currency="MXN")

        result = school_service.get_currency_for_school(db_session, school.id)

        assert result == "MXN"

    def test_get_unpaid_invoices_for_school_empty(self, db_session, db_helpers):
        school = db_helpers.create_school()

        result = school_service.get_unpaid_invoices_for_school(db_session, school.id)

        assert result == []

    def test_get_unpaid_invoices_for_school(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        db_helpers.create_invoice(student, status=InvoiceStatus.PENDING.value, amount_in_cents=5000)
        db_helpers.create_invoice(
            student, invoice_number="INV-002", status=InvoiceStatus.OVERDUE.value, amount_in_cents=10000
        )
        db_helpers.create_invoice(
            student, invoice_number="INV-003", status=InvoiceStatus.PAID.value, amount_in_cents=3000
        )

        result = school_service.get_unpaid_invoices_for_school(db_session, school.id)

        assert len(result) == 2
        assert result[0].amount_in_cents == 10000
        assert result[1].amount_in_cents == 5000

    def test_get_unpaid_invoices_for_school_respects_limit(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        for i in range(15):
            db_helpers.create_invoice(
                student,
                invoice_number=f"INV-{i:03d}",
                status=InvoiceStatus.PENDING.value,
                amount_in_cents=1000 * (i + 1),
            )

        result = school_service.get_unpaid_invoices_for_school(db_session, school.id, limit=5)

        assert len(result) == 5

    def test_get_recent_payments_for_school_empty(self, db_session, db_helpers):
        school = db_helpers.create_school()

        result = school_service.get_recent_payments_for_school(db_session, school.id)

        assert result == []

    def test_get_recent_payments_for_school(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        db_helpers.create_payment(student, amount_in_cents=5000)
        db_helpers.create_payment(student, amount_in_cents=10000)

        result = school_service.get_recent_payments_for_school(db_session, school.id)

        assert len(result) == 2

    def test_get_recent_payments_for_school_respects_limit(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        for i in range(15):
            db_helpers.create_payment(student, amount_in_cents=1000 * (i + 1))

        result = school_service.get_recent_payments_for_school(db_session, school.id, limit=5)

        assert len(result) == 5


class TestSchoolBalance:
    def test_get_school_balance_empty(self, db_session, db_helpers):
        school = db_helpers.create_school()

        result = school_service.get_school_balance(db_session, school.id)

        assert result.total_invoiced_cents == 0
        assert result.total_paid_cents == 0
        assert result.total_pending_cents == 0
        assert result.currency is None
        assert result.invoices == []
        assert result.payments == []

    def test_get_school_balance_with_data(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(
            student, amount_in_cents=10000, status=InvoiceStatus.PENDING.value, currency="COP"
        )
        payment = db_helpers.create_payment(student, amount_in_cents=3000)
        db_helpers.create_allocation(payment, invoice, amount_in_cents=3000)

        result = school_service.get_school_balance(db_session, school.id)

        assert result.total_invoiced_cents == 10000
        assert result.total_paid_cents == 3000
        assert result.total_pending_cents == 7000
        assert result.currency == "COP"
        assert len(result.invoices) == 1
        assert len(result.payments) == 1
