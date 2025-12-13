from app.db.models import InvoiceStatus, PaymentStatus


class TestPaymentAllocationList:
    def test_list_allocations_empty(self, client, admin_headers):
        response = client.get("/payment-allocation/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["limit"] == 100
        assert data["offset"] == 0
        assert data["pages"] == 0

    def test_list_allocations_with_data(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, invoice_number="INV-001")
        payment = db_helpers.create_payment(student)
        allocation = db_helpers.create_allocation(payment, invoice, amount_in_cents=5000)

        response = client.get("/payment-allocation/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == allocation.id
        assert data["items"][0]["amount_in_cents"] == 5000


class TestPaymentAllocationCreate:
    def test_create_allocation(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, invoice_number="INV-001")
        payment = db_helpers.create_payment(student)
        allocation_data = {
            "payment_id": payment.id,
            "invoice_id": invoice.id,
            "amount_in_cents": 5000
        }

        response = client.post("/payment-allocation/", json=allocation_data, headers=admin_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["payment_id"] == payment.id
        assert data["invoice_id"] == invoice.id
        assert data["amount_in_cents"] == 5000
        assert "id" in data
        assert "created_at" in data

        db_allocation = db_helpers.get_allocation(data["id"])
        assert db_allocation is not None
        assert db_allocation.payment_id == payment.id
        assert db_allocation.invoice_id == invoice.id
        assert db_allocation.amount_in_cents == 5000
        assert db_helpers.count_allocations() == 1

    def test_create_allocation_payment_not_found(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student)
        allocation_data = {
            "payment_id": 999,
            "invoice_id": invoice.id,
            "amount_in_cents": 5000
        }

        response = client.post("/payment-allocation/", json=allocation_data, headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "Payment not found"

    def test_create_allocation_invoice_not_found(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        payment = db_helpers.create_payment(student)
        allocation_data = {
            "payment_id": payment.id,
            "invoice_id": 999,
            "amount_in_cents": 5000
        }

        response = client.post("/payment-allocation/", json=allocation_data, headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "Invoice not found"


class TestPaymentAllocationGet:
    def test_get_allocation(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student)
        payment = db_helpers.create_payment(student)
        allocation = db_helpers.create_allocation(payment, invoice, amount_in_cents=5000)

        response = client.get(f"/payment-allocation/{allocation.id}", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == allocation.id
        assert data["payment_id"] == payment.id
        assert data["invoice_id"] == invoice.id
        assert data["amount_in_cents"] == 5000
        assert "created_at" in data

    def test_get_allocation_not_found(self, client, admin_headers):
        response = client.get("/payment-allocation/999", headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "Payment allocation not found"


class TestPaymentAllocationUpdate:
    def test_update_allocation(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student)
        payment = db_helpers.create_payment(student)
        allocation = db_helpers.create_allocation(payment, invoice, amount_in_cents=5000)

        update_data = {"amount_in_cents": 7000}
        response = client.put(f"/payment-allocation/{allocation.id}", json=update_data, headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["amount_in_cents"] == 7000

        db_allocation = db_helpers.get_allocation(allocation.id)
        assert db_allocation.amount_in_cents == 7000

    def test_update_allocation_not_found(self, client, admin_headers):
        response = client.put("/payment-allocation/999", json={"amount_in_cents": 5000}, headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "Payment allocation not found"


class TestPaymentAllocationDelete:
    def test_delete_allocation(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student)
        payment = db_helpers.create_payment(student)
        allocation = db_helpers.create_allocation(payment, invoice)
        allocation_id = allocation.id
        assert db_helpers.count_allocations() == 1

        response = client.delete(f"/payment-allocation/{allocation_id}", headers=admin_headers)

        assert response.status_code == 204
        assert db_helpers.get_allocation(allocation_id) is None
        assert db_helpers.count_allocations() == 0

    def test_delete_allocation_not_found(self, client, admin_headers):
        response = client.delete("/payment-allocation/999", headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "Payment allocation not found"


class TestPaymentAllocationInvoiceStatus:
    def test_allocation_updates_invoice_status_to_partially_paid(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(
            student, invoice_number="INV-001", amount_in_cents=10000, status=InvoiceStatus.PENDING.value
        )
        payment = db_helpers.create_payment(student, amount_in_cents=5000)

        allocation_data = {
            "payment_id": payment.id,
            "invoice_id": invoice.id,
            "amount_in_cents": 5000
        }
        response = client.post("/payment-allocation/", json=allocation_data, headers=admin_headers)
        assert response.status_code == 201

        db_invoice = db_helpers.get_invoice(invoice.id)
        assert db_invoice.status == InvoiceStatus.PARTIALLY_PAID.value

    def test_allocation_updates_invoice_status_to_paid(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(
            student, invoice_number="INV-001", amount_in_cents=10000, status=InvoiceStatus.PENDING.value
        )
        payment = db_helpers.create_payment(student, amount_in_cents=10000)

        allocation_data = {
            "payment_id": payment.id,
            "invoice_id": invoice.id,
            "amount_in_cents": 10000
        }
        response = client.post("/payment-allocation/", json=allocation_data, headers=admin_headers)
        assert response.status_code == 201

        db_invoice = db_helpers.get_invoice(invoice.id)
        assert db_invoice.status == InvoiceStatus.PAID.value

    def test_multiple_allocations_sum_to_paid(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(
            student, invoice_number="INV-001", amount_in_cents=10000, status=InvoiceStatus.PENDING.value
        )
        payment1 = db_helpers.create_payment(student, amount_in_cents=5000)
        payment2 = db_helpers.create_payment(student, amount_in_cents=5000)

        client.post("/payment-allocation/", json={
            "payment_id": payment1.id,
            "invoice_id": invoice.id,
            "amount_in_cents": 5000
        }, headers=admin_headers)

        db_invoice = db_helpers.get_invoice(invoice.id)
        assert db_invoice.status == InvoiceStatus.PARTIALLY_PAID.value

        client.post("/payment-allocation/", json={
            "payment_id": payment2.id,
            "invoice_id": invoice.id,
            "amount_in_cents": 5000
        }, headers=admin_headers)

        db_invoice = db_helpers.get_invoice(invoice.id)
        assert db_invoice.status == InvoiceStatus.PAID.value

    def test_pending_payment_not_counted_for_invoice_status(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(
            student, invoice_number="INV-001", amount_in_cents=10000, status=InvoiceStatus.PENDING.value
        )
        payment = db_helpers.create_payment(student, amount_in_cents=10000, status=PaymentStatus.PENDING.value)

        client.post("/payment-allocation/", json={
            "payment_id": payment.id,
            "invoice_id": invoice.id,
            "amount_in_cents": 10000
        }, headers=admin_headers)

        db_invoice = db_helpers.get_invoice(invoice.id)
        assert db_invoice.status == InvoiceStatus.PENDING.value

    def test_overpayment_still_marks_as_paid(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(
            student, invoice_number="INV-001", amount_in_cents=10000, status=InvoiceStatus.PENDING.value
        )
        payment = db_helpers.create_payment(student, amount_in_cents=15000)

        client.post("/payment-allocation/", json={
            "payment_id": payment.id,
            "invoice_id": invoice.id,
            "amount_in_cents": 15000
        }, headers=admin_headers)

        db_invoice = db_helpers.get_invoice(invoice.id)
        assert db_invoice.status == InvoiceStatus.PAID.value
