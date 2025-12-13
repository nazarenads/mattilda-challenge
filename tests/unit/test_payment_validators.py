"""Tests for payment validation rules."""

import pytest

from app.db.models import PaymentStatus
from app.validators.payment import (
    PaymentValidationError,
    validate_payment_update,
    validate_payment_delete,
)


class TestValidatePaymentUpdate:
    """Tests for validate_payment_update function."""

    def test_update_payment_without_allocations(self, db_session, db_helpers):
        """Test that updating a payment without allocations is allowed."""
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        payment = db_helpers.create_payment(student, amount_in_cents=10000)

        # Should not raise - no allocations
        validate_payment_update(db_session, payment, new_amount=5000)
        validate_payment_update(db_session, payment, new_status=PaymentStatus.PENDING.value)

    def test_cannot_change_amount_with_allocations(self, db_session, db_helpers):
        """Test that changing amount is blocked when payment has allocations."""
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student)
        payment = db_helpers.create_payment(student, amount_in_cents=10000)
        db_helpers.create_allocation(payment, invoice, amount_in_cents=5000)

        with pytest.raises(PaymentValidationError) as exc_info:
            validate_payment_update(db_session, payment, new_amount=8000)
        assert "Cannot modify amount of a payment that has allocations" in str(exc_info.value.detail)

    def test_same_amount_with_allocations_allowed(self, db_session, db_helpers):
        """Test that setting the same amount is allowed even with allocations."""
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student)
        payment = db_helpers.create_payment(student, amount_in_cents=10000)
        db_helpers.create_allocation(payment, invoice, amount_in_cents=5000)

        # Should not raise - same amount
        validate_payment_update(db_session, payment, new_amount=10000)

    def test_cannot_revert_completed_payment_with_allocations(self, db_session, db_helpers):
        """Test that reverting a completed payment with allocations is blocked."""
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student)
        payment = db_helpers.create_payment(
            student, amount_in_cents=10000, status=PaymentStatus.COMPLETED.value
        )
        db_helpers.create_allocation(payment, invoice, amount_in_cents=5000)

        # Cannot revert to pending
        with pytest.raises(PaymentValidationError) as exc_info:
            validate_payment_update(db_session, payment, new_status=PaymentStatus.PENDING.value)
        assert "Cannot revert a completed payment with allocations" in str(exc_info.value.detail)

        # Cannot revert to failed
        with pytest.raises(PaymentValidationError) as exc_info:
            validate_payment_update(db_session, payment, new_status=PaymentStatus.FAILED.value)
        assert "Cannot revert a completed payment with allocations" in str(exc_info.value.detail)

    def test_can_keep_completed_status_with_allocations(self, db_session, db_helpers):
        """Test that keeping completed status is allowed even with allocations."""
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student)
        payment = db_helpers.create_payment(
            student, amount_in_cents=10000, status=PaymentStatus.COMPLETED.value
        )
        db_helpers.create_allocation(payment, invoice, amount_in_cents=5000)

        # Should not raise - same status
        validate_payment_update(db_session, payment, new_status=PaymentStatus.COMPLETED.value)

    def test_pending_payment_can_change_status_with_allocations(self, db_session, db_helpers):
        """Test that non-completed payments can change status even with allocations."""
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student)
        # Note: This is an edge case - pending payments shouldn't have allocations
        # in normal flow, but the validator specifically checks completed->pending/failed
        payment = db_helpers.create_payment(
            student, amount_in_cents=10000, status=PaymentStatus.PENDING.value
        )
        db_helpers.create_allocation(payment, invoice, amount_in_cents=5000)

        # Should not raise - only blocks completed -> pending/failed
        validate_payment_update(db_session, payment, new_status=PaymentStatus.COMPLETED.value)

    def test_none_values_pass_validation(self, db_session, db_helpers):
        """Test that None values (no updates) pass validation."""
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student)
        payment = db_helpers.create_payment(student)
        db_helpers.create_allocation(payment, invoice)

        # Should not raise
        validate_payment_update(db_session, payment, new_status=None, new_amount=None)


class TestValidatePaymentDelete:
    """Tests for validate_payment_delete function."""

    def test_delete_payment_without_allocations(self, db_session, db_helpers):
        """Test that deleting a payment without allocations is allowed."""
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        payment = db_helpers.create_payment(student)

        # Should not raise
        validate_payment_delete(db_session, payment)

    def test_cannot_delete_payment_with_allocations(self, db_session, db_helpers):
        """Test that deleting a payment with allocations is blocked."""
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student)
        payment = db_helpers.create_payment(student)
        db_helpers.create_allocation(payment, invoice, amount_in_cents=5000)

        with pytest.raises(PaymentValidationError) as exc_info:
            validate_payment_delete(db_session, payment)
        assert "Cannot delete a payment that has allocations" in str(exc_info.value.detail)
        assert "Delete the allocations first" in str(exc_info.value.detail)

    def test_can_delete_after_allocations_removed(self, db_session, db_helpers):
        """Test that payment can be deleted after allocations are removed."""
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student)
        payment = db_helpers.create_payment(student)
        allocation = db_helpers.create_allocation(payment, invoice)

        # Delete the allocation first
        db_session.delete(allocation)
        db_session.commit()

        # Now deletion should be allowed
        validate_payment_delete(db_session, payment)
