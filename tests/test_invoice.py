from app.db.models import InvoiceStatus


class TestInvoiceList:
    def test_list_invoices_empty(self, client, admin_headers):
        response = client.get("/invoice/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["limit"] == 100
        assert data["offset"] == 0
        assert data["pages"] == 0

    def test_list_invoices_with_data(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice1 = db_helpers.create_invoice(student, invoice_number="INV-001", amount_in_cents=10000)
        invoice2 = db_helpers.create_invoice(student, invoice_number="INV-002", amount_in_cents=20000)

        response = client.get("/invoice/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["pages"] == 1
        invoice_numbers = [item["invoice_number"] for item in data["items"]]
        assert invoice1.invoice_number in invoice_numbers
        assert invoice2.invoice_number in invoice_numbers

    def test_list_invoices_pagination(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        for i in range(5):
            db_helpers.create_invoice(student, invoice_number=f"INV-00{i}", amount_in_cents=10000 * (i + 1))

        response = client.get("/invoice/?limit=2&offset=0", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["limit"] == 2
        assert data["offset"] == 0
        assert data["pages"] == 3

        response_page2 = client.get("/invoice/?limit=2&offset=2", headers=admin_headers)
        data_page2 = response_page2.json()
        assert len(data_page2["items"]) == 2
        assert data_page2["offset"] == 2


class TestInvoiceCreate:
    def test_create_invoice(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice_data = {
            "invoice_number": "INV-001",
            "amount_in_cents": 10050,
            "currency": "USD",
            "status": "pending",
            "issue_date": "2024-01-01T00:00:00",
            "due_date": "2024-02-01T00:00:00",
            "description": "Monthly fee",
            "student_id": student.id
        }

        response = client.post("/invoice/", json=invoice_data, headers=admin_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["invoice_number"] == "INV-001"
        assert data["amount_in_cents"] == 10050
        assert data["currency"] == "USD"
        assert data["status"] == "pending"
        assert data["description"] == "Monthly fee"
        assert data["student_id"] == student.id
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

        db_invoice = db_helpers.get_invoice(data["id"])
        assert db_invoice is not None
        assert db_invoice.invoice_number == "INV-001"
        assert db_invoice.amount_in_cents == 10050
        assert db_invoice.currency == "USD"
        assert db_helpers.count_invoices() == 1

    def test_create_invoice_student_not_found(self, client, admin_headers):
        invoice_data = {
            "invoice_number": "INV-001",
            "amount_in_cents": 10050,
            "currency": "USD",
            "status": "pending",
            "issue_date": "2024-01-01T00:00:00",
            "due_date": "2024-02-01T00:00:00",
            "student_id": 999
        }

        response = client.post("/invoice/", json=invoice_data, headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "Student not found"

    def test_create_invoice_with_default_status(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice_data = {
            "invoice_number": "INV-001",
            "amount_in_cents": 10000,
            "currency": "USD",
            "issue_date": "2024-01-01T00:00:00",
            "due_date": "2024-02-01T00:00:00",
            "student_id": student.id
        }

        response = client.post("/invoice/", json=invoice_data, headers=admin_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"


class TestInvoiceGet:
    def test_get_invoice(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(
            student,
            invoice_number="INV-001",
            amount_in_cents=10050,
            description="Test invoice"
        )

        response = client.get(f"/invoice/{invoice.id}", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == invoice.id
        assert data["invoice_number"] == "INV-001"
        assert data["amount_in_cents"] == 10050
        assert data["currency"] == "USD"
        assert data["status"] == "pending"
        assert data["description"] == "Test invoice"
        assert data["student_id"] == student.id
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_invoice_not_found(self, client, admin_headers):
        response = client.get("/invoice/999", headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "Invoice not found"


class TestInvoiceUpdate:
    def test_update_invoice(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(
            student,
            invoice_number="INV-001",
            amount_in_cents=10000,
            status=InvoiceStatus.PENDING.value
        )
        original_created_at = invoice.created_at

        update_data = {"status": "paid", "amount_in_cents": 15000}
        response = client.put(f"/invoice/{invoice.id}", json=update_data, headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paid"
        assert data["amount_in_cents"] == 15000
        assert data["invoice_number"] == "INV-001"

        db_invoice = db_helpers.get_invoice(invoice.id)
        assert db_invoice.status == "paid"
        assert db_invoice.amount_in_cents == 15000
        assert db_invoice.created_at == original_created_at
        assert db_invoice.updated_at > original_created_at

    def test_update_invoice_not_found(self, client, admin_headers):
        response = client.put("/invoice/999", json={"status": "paid"}, headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "Invoice not found"

    def test_update_invoice_student_not_found(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student)

        response = client.put(f"/invoice/{invoice.id}", json={"student_id": 999}, headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "Student not found"


class TestInvoiceDelete:
    def test_delete_invoice(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student)
        invoice_id = invoice.id
        assert db_helpers.count_invoices() == 1

        response = client.delete(f"/invoice/{invoice_id}", headers=admin_headers)

        assert response.status_code == 204
        assert db_helpers.get_invoice(invoice_id) is None
        assert db_helpers.count_invoices() == 0

    def test_delete_invoice_not_found(self, client, admin_headers):
        response = client.delete("/invoice/999", headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "Invoice not found"
