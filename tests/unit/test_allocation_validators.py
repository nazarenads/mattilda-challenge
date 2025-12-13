"""Tests for allocation validation rules."""

import pytest

from app.db.models import InvoiceStatus, PaymentStatus
from app.validators.allocation import (
    AllocationValidationError,
    validate_allocation_create,
    validate_allocation_update,
    get_payment_allocated_amount,
)


class TestValidateAllocationCreate:
    """Tests for validate_allocation_create function."""

    def test_valid_allocation(self, db_session, db_helpers):
        """Test that a valid allocation passes validation."""
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, amount_in_cents=10000, currency="USD")
        payment = db_helpers.create_payment(
            student, amount_in_cents=10000, currency="USD", status=PaymentStatus.COMPLETED.value
        )

        # Should not raise
        validate_allocation_create(db_session, payment, invoice, 5000)

    def test_amount_must_be_positive(self, db_session, db_helpers):
        """Test that allocation amount must be positive."""
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, currency="USD")
        payment = db_helpers.create_payment(student, currency="USD")

        with pytest.raises(AllocationValidationError) as exc_info:
            validate_allocation_create(db_session, payment, invoice, 0)
        assert "Allocation amount must be positive" in str(exc_info.value.detail)

        with pytest.raises(AllocationValidationError) as exc_info:
            validate_allocation_create(db_session, payment, invoice, -100)
        assert "Allocation amount must be positive" in str(exc_info.value.detail)

    def test_payment_must_be_completed(self, db_session, db_helpers):
        """Test that payment must be completed to allocate from it."""
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, currency="USD")

        # Test with pending payment
        pending_payment = db_helpers.create_payment(
            student, currency="USD", status=PaymentStatus.PENDING.value
        )
        with pytest.raises(AllocationValidationError) as exc_info:
            validate_allocation_create(db_session, pending_payment, invoice, 5000)
        assert "Payment must be completed" in str(exc_info.value.detail)

        # Test with failed payment
        failed_payment = db_helpers.create_payment(
            student, currency="USD", status=PaymentStatus.FAILED.value
        )
        with pytest.raises(AllocationValidationError) as exc_info:
            validate_allocation_create(db_session, failed_payment, invoice, 5000)
        assert "Payment must be completed" in str(exc_info.value.detail)

    def test_cannot_allocate_to_cancelled_invoice(self, db_session, db_helpers):
        """Test that cannot allocate to a cancelled invoice."""
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        cancelled_invoice = db_helpers.create_invoice(
            student, currency="USD", status=InvoiceStatus.CANCELLED.value
        )
        payment = db_helpers.create_payment(student, currency="USD")

        with pytest.raises(AllocationValidationError) as exc_info:
            validate_allocation_create(db_session, payment, cancelled_invoice, 5000)
        assert "Cannot allocate to a cancelled invoice" in str(exc_info.value.detail)

    def test_currency_must_match(self, db_session, db_helpers):
        """Test that payment and invoice currencies must match."""
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        usd_invoice = db_helpers.create_invoice(student, currency="USD")
        mxn_payment = db_helpers.create_payment(student, currency="MXN")

        with pytest.raises(AllocationValidationError) as exc_info:
            validate_allocation_create(db_session, mxn_payment, usd_invoice, 5000)
        assert "Currency mismatch" in str(exc_info.value.detail)
        assert "MXN" in str(exc_info.value.detail)
        assert "USD" in str(exc_info.value.detail)

    def test_cannot_exceed_payment_available_balance(self, db_session, db_helpers):
        """Test that allocation cannot exceed payment's available balance."""
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, amount_in_cents=20000, currency="USD")
        payment = db_helpers.create_payment(
            student, amount_in_cents=10000, currency="USD"
        )

        # Try to allocate more than payment amount
        with pytest.raises(AllocationValidationError) as exc_info:
            validate_allocation_create(db_session, payment, invoice, 15000)
        assert "exceeds available payment balance" in str(exc_info.value.detail)

    def test_cannot_exceed_payment_balance_with_existing_allocations(self, db_session, db_helpers):
        """Test that allocation considers existing allocations."""
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice1 = db_helpers.create_invoice(
            student, invoice_number="INV-001", amount_in_cents=10000, currency="USD"
        )
        invoice2 = db_helpers.create_invoice(
            student, invoice_number="INV-002", amount_in_cents=10000, currency="USD"
        )
        payment = db_helpers.create_payment(
            student, amount_in_cents=10000, currency="USD"
        )

        # Create first allocation for half the payment
        db_helpers.create_allocation(payment, invoice1, amount_in_cents=6000)

        # Try to allocate more than remaining balance
        with pytest.raises(AllocationValidationError) as exc_info:
            validate_allocation_create(db_session, payment, invoice2, 5000)
        assert "exceeds available payment balance" in str(exc_info.value.detail)
        assert "already allocated: 6000" in str(exc_info.value.detail)

    def test_overpayment_to_invoice_is_allowed(self, db_session, db_helpers):
        """Test that allocating more than invoice amount is allowed (overpayment)."""
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, amount_in_cents=5000, currency="USD")
        payment = db_helpers.create_payment(
            student, amount_in_cents=10000, currency="USD"
        )

        # Allocating more than invoice amount should NOT raise
        validate_allocation_create(db_session, payment, invoice, 8000)

    def test_allocate_to_paid_invoice_is_allowed(self, db_session, db_helpers):
        """Test that allocating to an already paid invoice is allowed."""
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        paid_invoice = db_helpers.create_invoice(
            student, currency="USD", status=InvoiceStatus.PAID.value
        )
        payment = db_helpers.create_payment(student, currency="USD")

        # Should NOT raise - overpayments are allowed
        validate_allocation_create(db_session, payment, paid_invoice, 5000)


class TestGetPaymentAllocatedAmount:
    """Tests for get_payment_allocated_amount helper function."""

    def test_no_allocations_returns_zero(self, db_session, db_helpers):
        """Test that a payment with no allocations returns 0."""
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        payment = db_helpers.create_payment(student)

        result = get_payment_allocated_amount(db_session, payment.id)
        assert result == 0

    def test_single_allocation(self, db_session, db_helpers):
        """Test with a single allocation."""
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student)
        payment = db_helpers.create_payment(student, amount_in_cents=10000)
        db_helpers.create_allocation(payment, invoice, amount_in_cents=5000)

        result = get_payment_allocated_amount(db_session, payment.id)
        assert result == 5000

    def test_multiple_allocations(self, db_session, db_helpers):
        """Test with multiple allocations to different invoices."""
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice1 = db_helpers.create_invoice(student, invoice_number="INV-001")
        invoice2 = db_helpers.create_invoice(student, invoice_number="INV-002")
        payment = db_helpers.create_payment(student, amount_in_cents=10000)
        db_helpers.create_allocation(payment, invoice1, amount_in_cents=3000)
        db_helpers.create_allocation(payment, invoice2, amount_in_cents=4000)

        result = get_payment_allocated_amount(db_session, payment.id)
        assert result == 7000


class TestValidateAllocationUpdate:
    """Tests for validate_allocation_update function."""

    def test_valid_update(self, db_session, db_helpers):
        """Test that a valid update passes validation."""
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, amount_in_cents=10000, currency="USD")
        payment = db_helpers.create_payment(
            student, amount_in_cents=10000, currency="USD"
        )
        allocation = db_helpers.create_allocation(payment, invoice, amount_in_cents=5000)

        # Should not raise - updating within payment balance
        validate_allocation_update(db_session, allocation, 7000)

    def test_none_amount_passes(self, db_session, db_helpers):
        """Test that None amount (no update) passes validation."""
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, currency="USD")
        payment = db_helpers.create_payment(student, currency="USD")
        allocation = db_helpers.create_allocation(payment, invoice)

        # Should not raise
        validate_allocation_update(db_session, allocation, None)

    def test_amount_must_be_positive(self, db_session, db_helpers):
        """Test that updated amount must be positive."""
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, currency="USD")
        payment = db_helpers.create_payment(student, currency="USD")
        allocation = db_helpers.create_allocation(payment, invoice)

        with pytest.raises(AllocationValidationError) as exc_info:
            validate_allocation_update(db_session, allocation, 0)
        assert "Allocation amount must be positive" in str(exc_info.value.detail)

    def test_cannot_exceed_payment_balance(self, db_session, db_helpers):
        """Test that updated amount cannot exceed payment available balance."""
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, currency="USD")
        payment = db_helpers.create_payment(student, amount_in_cents=10000, currency="USD")
        allocation = db_helpers.create_allocation(payment, invoice, amount_in_cents=5000)

        # Try to update to more than payment total
        with pytest.raises(AllocationValidationError) as exc_info:
            validate_allocation_update(db_session, allocation, 15000)
        assert "exceeds available payment balance" in str(exc_info.value.detail)

    def test_update_considers_current_allocation(self, db_session, db_helpers):
        """Test that update correctly considers current allocation amount."""
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, currency="USD")
        payment = db_helpers.create_payment(student, amount_in_cents=10000, currency="USD")
        allocation = db_helpers.create_allocation(payment, invoice, amount_in_cents=5000)

        # Updating to full payment amount should work (5000 current + 5000 available = 10000)
        validate_allocation_update(db_session, allocation, 10000)
