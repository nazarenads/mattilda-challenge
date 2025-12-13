from datetime import datetime

from app.db.models import Payment, PaymentStatus, PaymentMethod
from app.schemas import PaymentUpdate
from app.services import payment as payment_service


class TestPaymentServiceCRUD:
    def test_create_payment(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        now = datetime.now()
        payment = Payment(
            amount_in_cents=10000,
            status=PaymentStatus.COMPLETED.value,
            payment_method=PaymentMethod.CARD.value,
            student_id=student.id,
            created_at=now,
            updated_at=now,
        )

        result = payment_service.create_payment(db_session, payment)

        assert result.id is not None
        assert result.amount_in_cents == 10000
        assert result.status == PaymentStatus.COMPLETED.value
        assert result.payment_method == PaymentMethod.CARD.value
        assert result.student_id == student.id

    def test_get_payment_by_id(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        payment = db_helpers.create_payment(student, amount_in_cents=5000)

        result = payment_service.get_payment_by_id(db_session, payment.id)

        assert result is not None
        assert result.id == payment.id
        assert result.amount_in_cents == 5000

    def test_get_payment_by_id_not_found(self, db_session):
        result = payment_service.get_payment_by_id(db_session, 9999)

        assert result is None

    def test_get_payments(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        db_helpers.create_payment(student, amount_in_cents=1000)
        db_helpers.create_payment(student, amount_in_cents=2000)
        db_helpers.create_payment(student, amount_in_cents=3000)

        result = payment_service.get_payments(db_session)

        assert len(result) == 3
        amounts = [p.amount_in_cents for p in result]
        assert 1000 in amounts
        assert 2000 in amounts
        assert 3000 in amounts

    def test_get_payments_with_pagination(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        for i in range(5):
            db_helpers.create_payment(student, amount_in_cents=1000 * (i + 1))

        result = payment_service.get_payments(db_session, offset=2, limit=2)

        assert len(result) == 2

    def test_get_payments_with_count(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        db_helpers.create_payment(student, amount_in_cents=1000)
        db_helpers.create_payment(student, amount_in_cents=2000)

        items, total = payment_service.get_payments_with_count(db_session)

        assert total == 2
        assert len(items) == 2

    def test_get_payments_with_count_pagination(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        for i in range(5):
            db_helpers.create_payment(student, amount_in_cents=1000 * (i + 1))

        items, total = payment_service.get_payments_with_count(db_session, offset=0, limit=2)

        assert total == 5
        assert len(items) == 2

    def test_get_payments_by_school_with_count(self, db_session, db_helpers):
        school1 = db_helpers.create_school(name="School 1")
        school2 = db_helpers.create_school(name="School 2", tax_id="222")
        student1 = db_helpers.create_student(school1, identifier="S1")
        student2 = db_helpers.create_student(school2, identifier="S2", email="s2@example.com")
        db_helpers.create_payment(student1, amount_in_cents=1000)
        db_helpers.create_payment(student1, amount_in_cents=2000)
        db_helpers.create_payment(student2, amount_in_cents=3000)

        items, total = payment_service.get_payments_by_school_with_count(db_session, school1.id)

        assert total == 2
        assert len(items) == 2
        for payment in items:
            assert payment.student.school_id == school1.id

    def test_update_payment(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        payment = db_helpers.create_payment(student, amount_in_cents=10000, status=PaymentStatus.PENDING.value)
        update_data = PaymentUpdate(status=PaymentStatus.COMPLETED.value)

        result = payment_service.update_payment(db_session, payment, update_data)

        assert result.status == PaymentStatus.COMPLETED.value
        assert result.id == payment.id

    def test_update_payment_partial(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        payment = db_helpers.create_payment(
            student,
            amount_in_cents=10000,
            status=PaymentStatus.PENDING.value,
            payment_method=PaymentMethod.CARD.value,
        )
        update_data = PaymentUpdate(amount_in_cents=15000)

        result = payment_service.update_payment(db_session, payment, update_data)

        assert result.amount_in_cents == 15000
        assert result.status == PaymentStatus.PENDING.value
        assert result.payment_method == PaymentMethod.CARD.value

    def test_update_payment_method(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        payment = db_helpers.create_payment(student, payment_method=PaymentMethod.CARD.value)
        update_data = PaymentUpdate(payment_method=PaymentMethod.BANK_TRANSFER.value)

        result = payment_service.update_payment(db_session, payment, update_data)

        assert result.payment_method == PaymentMethod.BANK_TRANSFER.value

    def test_delete_payment(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        payment = db_helpers.create_payment(student)
        payment_id = payment.id

        payment_service.delete_payment(db_session, payment)

        assert payment_service.get_payment_by_id(db_session, payment_id) is None


class TestPaymentServiceFiltering:
    def test_get_payments_by_school_excludes_other_schools(self, db_session, db_helpers):
        school1 = db_helpers.create_school(name="School 1")
        school2 = db_helpers.create_school(name="School 2", tax_id="222")
        student1 = db_helpers.create_student(school1, identifier="S1")
        student2 = db_helpers.create_student(school2, identifier="S2", email="s2@example.com")
        db_helpers.create_payment(student1, amount_in_cents=1000)
        db_helpers.create_payment(student2, amount_in_cents=2000)

        items, total = payment_service.get_payments_by_school_with_count(db_session, school1.id)

        assert total == 1
        assert items[0].amount_in_cents == 1000

    def test_get_payments_by_school_with_pagination(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        for i in range(10):
            db_helpers.create_payment(student, amount_in_cents=1000 * (i + 1))

        items, total = payment_service.get_payments_by_school_with_count(db_session, school.id, limit=3, offset=0)

        assert total == 10
        assert len(items) == 3


class TestPaymentStatuses:
    def test_create_payment_with_different_statuses(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)

        for status in [PaymentStatus.PENDING, PaymentStatus.COMPLETED, PaymentStatus.FAILED]:
            payment = db_helpers.create_payment(student, status=status.value)
            result = payment_service.get_payment_by_id(db_session, payment.id)
            assert result.status == status.value

    def test_create_payment_with_different_methods(self, db_session, db_helpers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)

        for method in [PaymentMethod.CARD, PaymentMethod.BANK_TRANSFER, PaymentMethod.CASH]:
            payment = db_helpers.create_payment(student, payment_method=method.value)
            result = payment_service.get_payment_by_id(db_session, payment.id)
            assert result.payment_method == method.value
