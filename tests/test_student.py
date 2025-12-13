from app.db.models import InvoiceStatus, PaymentStatus


class TestStudentList:
    def test_list_students_empty(self, client, admin_headers):
        response = client.get("/student/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["limit"] == 100
        assert data["offset"] == 0
        assert data["pages"] == 0

    def test_list_students_with_data(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student1 = db_helpers.create_student(school, identifier="ID-001", name="Student 1", email="s1@example.com")
        student2 = db_helpers.create_student(school, identifier="ID-002", name="Student 2", email="s2@example.com")

        response = client.get("/student/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["pages"] == 1
        student_names = [item["name"] for item in data["items"]]
        assert student1.name in student_names
        assert student2.name in student_names

    def test_list_students_pagination(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        for i in range(5):
            db_helpers.create_student(school, identifier=f"ID-{i}", name=f"Student {i}", email=f"s{i}@example.com")

        response = client.get("/student/?limit=2&offset=0", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["limit"] == 2
        assert data["offset"] == 0
        assert data["pages"] == 3

        response_page2 = client.get("/student/?limit=2&offset=2", headers=admin_headers)
        data_page2 = response_page2.json()
        assert len(data_page2["items"]) == 2
        assert data_page2["offset"] == 2


class TestStudentCreate:
    def test_create_student(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student_data = {
            "identifier": "ID-001",
            "name": "John Doe",
            "email": "john@example.com",
            "school_id": school.id
        }

        response = client.post("/student/", json=student_data, headers=admin_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["identifier"] == "ID-001"
        assert data["name"] == "John Doe"
        assert data["email"] == "john@example.com"
        assert data["school_id"] == school.id
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

        db_student = db_helpers.get_student(data["id"])
        assert db_student is not None
        assert db_student.identifier == "ID-001"
        assert db_student.name == "John Doe"
        assert db_student.email == "john@example.com"
        assert db_helpers.count_students() == 1

    def test_create_student_school_not_found(self, client, admin_headers):
        student_data = {
            "identifier": "ID-001",
            "name": "John Doe",
            "email": "john@example.com",
            "school_id": 999
        }

        response = client.post("/student/", json=student_data, headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "School not found"


class TestStudentGet:
    def test_get_student(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school, identifier="ID-001", name="John Doe", email="john@example.com")

        response = client.get(f"/student/{student.id}", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == student.id
        assert data["identifier"] == "ID-001"
        assert data["name"] == "John Doe"
        assert data["email"] == "john@example.com"
        assert data["school_id"] == school.id
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_student_not_found(self, client, admin_headers):
        response = client.get("/student/999", headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "Student not found"


class TestStudentUpdate:
    def test_update_student(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school, identifier="ID-001", name="Original Name", email="original@example.com")
        original_created_at = student.created_at

        update_data = {"name": "Updated Name", "email": "updated@example.com"}
        response = client.put(f"/student/{student.id}", json=update_data, headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["email"] == "updated@example.com"
        assert data["identifier"] == "ID-001"

        db_student = db_helpers.get_student(student.id)
        assert db_student.name == "Updated Name"
        assert db_student.email == "updated@example.com"
        assert db_student.created_at == original_created_at
        assert db_student.updated_at > original_created_at

    def test_update_student_not_found(self, client, admin_headers):
        response = client.put("/student/999", json={"name": "New Name"}, headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "Student not found"

    def test_update_student_school_not_found(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)

        response = client.put(f"/student/{student.id}", json={"school_id": 999}, headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "School not found"


class TestStudentDelete:
    def test_delete_student(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        student_id = student.id
        assert db_helpers.count_students() == 1

        response = client.delete(f"/student/{student_id}", headers=admin_headers)

        assert response.status_code == 204
        assert db_helpers.get_student(student_id) is None
        assert db_helpers.count_students() == 0

    def test_delete_student_not_found(self, client, admin_headers):
        response = client.delete("/student/999", headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "Student not found"


class TestStudentBalance:
    def test_get_student_balance_empty(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)

        response = client.get(f"/student/{student.id}/balance", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total_invoiced_cents"] == 0
        assert data["total_paid_cents"] == 0
        assert data["total_pending_cents"] == 0
        assert data["currency"] is None
        assert data["invoices"] == []
        assert data["payments"] == []

    def test_get_student_balance_with_data(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)

        invoice1 = db_helpers.create_invoice(
            student, invoice_number="INV-001", amount_in_cents=10000, status=InvoiceStatus.PENDING.value
        )
        db_helpers.create_invoice(
            student, invoice_number="INV-002", amount_in_cents=5000, status=InvoiceStatus.OVERDUE.value
        )

        payment = db_helpers.create_payment(student, amount_in_cents=3000)
        db_helpers.create_allocation(payment, invoice1, amount_in_cents=3000)

        response = client.get(f"/student/{student.id}/balance", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total_invoiced_cents"] == 15000
        assert data["total_paid_cents"] == 3000
        assert data["total_pending_cents"] == 12000
        assert data["currency"] == "USD"
        assert len(data["invoices"]) == 2
        assert len(data["payments"]) == 1

        payment_data = data["payments"][0]
        assert payment_data["amount_in_cents"] == 3000
        assert payment_data["status"] == "completed"

    def test_get_student_balance_not_found(self, client, admin_headers):
        response = client.get("/student/999/balance", headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "Student not found"

    def test_get_student_balance_excludes_pending_payments(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        invoice = db_helpers.create_invoice(student, amount_in_cents=10000)

        pending_payment = db_helpers.create_payment(
            student, amount_in_cents=10000, status=PaymentStatus.PENDING.value
        )
        db_helpers.create_allocation(pending_payment, invoice, amount_in_cents=10000)

        response = client.get(f"/student/{student.id}/balance", headers=admin_headers)

        data = response.json()
        assert data["total_invoiced_cents"] == 10000
        assert data["total_paid_cents"] == 0
        assert data["total_pending_cents"] == 10000
