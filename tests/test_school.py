from app.db.models import InvoiceStatus, PaymentStatus


class TestSchoolList:
    def test_list_schools_empty(self, client, admin_headers):
        response = client.get("/school/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["limit"] == 100
        assert data["offset"] == 0
        assert data["pages"] == 0

    def test_list_schools_with_data(self, client, db_helpers, admin_headers):
        school1 = db_helpers.create_school(name="School 1", country="US", tax_id="111")
        school2 = db_helpers.create_school(name="School 2", country="UK", tax_id="222")

        response = client.get("/school/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["pages"] == 1
        school_names = [item["name"] for item in data["items"]]
        assert school1.name in school_names
        assert school2.name in school_names

    def test_list_schools_pagination(self, client, db_helpers, admin_headers):
        for i in range(5):
            db_helpers.create_school(name=f"School {i}", country="US", tax_id=f"{i}")

        response = client.get("/school/?limit=2&offset=0", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["limit"] == 2
        assert data["offset"] == 0
        assert data["pages"] == 3

        response_page2 = client.get("/school/?limit=2&offset=2", headers=admin_headers)
        data_page2 = response_page2.json()
        assert len(data_page2["items"]) == 2
        assert data_page2["offset"] == 2

    def test_list_schools_as_non_admin_forbidden(self, client, school_user_headers):
        """Non-admin users cannot list all schools."""
        response = client.get("/school/", headers=school_user_headers)

        assert response.status_code == 403
        assert response.json()["detail"] == "Admin access required"


class TestSchoolCreate:
    def test_create_school(self, client, db_helpers, admin_headers):
        school_data = {
            "name": "Test School",
            "country": "US",
            "tax_id": "123456789"
        }

        response = client.post("/school/", json=school_data, headers=admin_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test School"
        assert data["country"] == "US"
        assert data["tax_id"] == "123456789"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

        db_school = db_helpers.get_school(data["id"])
        assert db_school is not None
        assert db_school.name == "Test School"
        assert db_school.country == "US"
        assert db_school.tax_id == "123456789"
        assert db_helpers.count_schools() == 1


class TestSchoolGet:
    def test_get_school(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school(name="Test School", country="US", tax_id="123")

        response = client.get(f"/school/{school.id}", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == school.id
        assert data["name"] == "Test School"
        assert data["country"] == "US"
        assert data["tax_id"] == "123"
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_school_not_found(self, client, admin_headers):
        response = client.get("/school/999", headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "School not found"


class TestSchoolUpdate:
    def test_update_school(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school(name="Original Name", country="US", tax_id="123")
        original_created_at = school.created_at

        update_data = {"name": "Updated Name", "country": "UK"}
        response = client.put(f"/school/{school.id}", json=update_data, headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["country"] == "UK"
        assert data["tax_id"] == "123"

        db_school = db_helpers.get_school(school.id)
        assert db_school.name == "Updated Name"
        assert db_school.country == "UK"
        assert db_school.created_at == original_created_at
        assert db_school.updated_at > original_created_at

    def test_update_school_not_found(self, client, admin_headers):
        response = client.put("/school/999", json={"name": "New Name"}, headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "School not found"


class TestSchoolDelete:
    def test_delete_school(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school(name="To Delete", country="US", tax_id="123")
        school_id = school.id
        assert db_helpers.count_schools() == 1

        response = client.delete(f"/school/{school_id}", headers=admin_headers)

        assert response.status_code == 204
        assert db_helpers.get_school(school_id) is None
        assert db_helpers.count_schools() == 0

    def test_delete_school_not_found(self, client, admin_headers):
        response = client.delete("/school/999", headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "School not found"


class TestSchoolBalance:
    def test_get_school_balance_empty(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()

        response = client.get(f"/school/{school.id}/balance", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total_invoiced_cents"] == 0
        assert data["total_paid_cents"] == 0
        assert data["total_pending_cents"] == 0
        assert data["currency"] is None
        assert data["invoices"] == []
        assert data["payments"] == []

    def test_get_school_balance_with_data(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student1 = db_helpers.create_student(school, identifier="ID-001", email="s1@example.com")
        student2 = db_helpers.create_student(school, identifier="ID-002", email="s2@example.com")

        invoice1 = db_helpers.create_invoice(
            student1,
            invoice_number="INV-001",
            amount_in_cents=10000,
            status=InvoiceStatus.OVERDUE.value,
        )
        db_helpers.create_invoice(
            student2,
            invoice_number="INV-002",
            amount_in_cents=5000,
            status=InvoiceStatus.PENDING.value,
        )

        payment = db_helpers.create_payment(student1, amount_in_cents=4000)
        db_helpers.create_allocation(payment, invoice1, amount_in_cents=4000)

        response = client.get(f"/school/{school.id}/balance", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total_invoiced_cents"] == 15000
        assert data["total_paid_cents"] == 4000
        assert data["total_pending_cents"] == 11000
        assert data["currency"] == "USD"
        assert len(data["invoices"]) == 2
        assert len(data["payments"]) == 1

        invoice_amounts = [inv["amount_in_cents"] for inv in data["invoices"]]
        assert invoice_amounts[0] >= invoice_amounts[1]

    def test_get_school_balance_not_found(self, client, admin_headers):
        response = client.get("/school/999/balance", headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "School not found"

    def test_get_school_balance_excludes_pending_payments(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, amount_in_cents=10000)

        pending_payment = db_helpers.create_payment(
            student, amount_in_cents=10000, status=PaymentStatus.PENDING.value
        )
        db_helpers.create_allocation(pending_payment, invoice, amount_in_cents=10000)

        response = client.get(f"/school/{school.id}/balance", headers=admin_headers)

        data = response.json()
        assert data["total_invoiced_cents"] == 10000
        assert data["total_paid_cents"] == 0
        assert data["total_pending_cents"] == 10000
