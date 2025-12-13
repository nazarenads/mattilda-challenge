from app.db.models import PaymentStatus, PaymentMethod


class TestPaymentList:
    def test_list_payments_empty(self, client, admin_headers):
        response = client.get("/payment/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["limit"] == 100
        assert data["offset"] == 0
        assert data["pages"] == 0

    def test_list_payments_with_data(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        payment1 = db_helpers.create_payment(student, amount_in_cents=10000, status=PaymentStatus.PENDING.value)
        payment2 = db_helpers.create_payment(student, amount_in_cents=20000, status=PaymentStatus.COMPLETED.value)

        response = client.get("/payment/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["pages"] == 1
        payment_amounts = [item["amount_in_cents"] for item in data["items"]]
        assert payment1.amount_in_cents in payment_amounts
        assert payment2.amount_in_cents in payment_amounts

    def test_list_payments_pagination(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        for i in range(5):
            db_helpers.create_payment(student, amount_in_cents=10000 * (i + 1))

        response = client.get("/payment/?limit=2&offset=0", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["limit"] == 2
        assert data["offset"] == 0
        assert data["pages"] == 3

        response_page2 = client.get("/payment/?limit=2&offset=2", headers=admin_headers)
        data_page2 = response_page2.json()
        assert len(data_page2["items"]) == 2
        assert data_page2["offset"] == 2


class TestPaymentCreate:
    def test_create_payment(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        payment_data = {
            "amount_in_cents": 10000,
            "status": "completed",
            "payment_method": "card",
            "student_id": student.id
        }

        response = client.post("/payment/", json=payment_data, headers=admin_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["amount_in_cents"] == 10000
        assert data["status"] == "completed"
        assert data["payment_method"] == "card"
        assert data["student_id"] == student.id
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

        db_payment = db_helpers.get_payment(data["id"])
        assert db_payment is not None
        assert db_payment.amount_in_cents == 10000
        assert db_payment.status == "completed"
        assert db_payment.payment_method == "card"
        assert db_helpers.count_payments() == 1

    def test_create_payment_student_not_found(self, client, admin_headers):
        payment_data = {
            "amount_in_cents": 10000,
            "status": "pending",
            "payment_method": "cash",
            "student_id": 999
        }

        response = client.post("/payment/", json=payment_data, headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "Student not found"

    def test_create_payment_with_different_methods(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)

        for method in ["cash", "card", "bank_transfer"]:
            payment_data = {
                "amount_in_cents": 10000,
                "status": "completed",
                "payment_method": method,
                "student_id": student.id
            }
            response = client.post("/payment/", json=payment_data, headers=admin_headers)
            assert response.status_code == 201
            assert response.json()["payment_method"] == method

        assert db_helpers.count_payments() == 3


class TestPaymentGet:
    def test_get_payment(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        payment = db_helpers.create_payment(
            student,
            amount_in_cents=10000,
            status=PaymentStatus.PENDING.value,
            payment_method=PaymentMethod.BANK_TRANSFER.value
        )

        response = client.get(f"/payment/{payment.id}", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == payment.id
        assert data["amount_in_cents"] == 10000
        assert data["status"] == "pending"
        assert data["payment_method"] == "bank_transfer"
        assert data["student_id"] == student.id
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_payment_not_found(self, client, admin_headers):
        response = client.get("/payment/999", headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "Payment not found"


class TestPaymentUpdate:
    def test_update_payment(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        payment = db_helpers.create_payment(
            student,
            amount_in_cents=10000,
            status=PaymentStatus.PENDING.value
        )
        original_created_at = payment.created_at

        update_data = {"status": "completed", "amount_in_cents": 15000}
        response = client.put(f"/payment/{payment.id}", json=update_data, headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["amount_in_cents"] == 15000

        db_payment = db_helpers.get_payment(payment.id)
        assert db_payment.status == "completed"
        assert db_payment.amount_in_cents == 15000
        assert db_payment.created_at == original_created_at
        assert db_payment.updated_at > original_created_at

    def test_update_payment_not_found(self, client, admin_headers):
        response = client.put("/payment/999", json={"status": "completed"}, headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "Payment not found"

    def test_update_payment_student_not_found(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        payment = db_helpers.create_payment(student)

        response = client.put(f"/payment/{payment.id}", json={"student_id": 999}, headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "Student not found"


class TestPaymentDelete:
    def test_delete_payment(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()
        student = db_helpers.create_student(school)
        payment = db_helpers.create_payment(student)
        payment_id = payment.id
        assert db_helpers.count_payments() == 1

        response = client.delete(f"/payment/{payment_id}", headers=admin_headers)

        assert response.status_code == 204
        assert db_helpers.get_payment(payment_id) is None
        assert db_helpers.count_payments() == 0

    def test_delete_payment_not_found(self, client, admin_headers):
        response = client.delete("/payment/999", headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "Payment not found"
