import pytest


@pytest.fixture
def school(client):
    response = client.post("/school/", json={
        "name": "Test School",
        "country": "US",
        "tax_id": "123456789"
    })
    return response.json()


@pytest.fixture
def student(client, school):
    response = client.post("/student/", json={
        "identifier": "ID-001",
        "name": "Test Student",
        "email": "student@example.com",
        "school_id": school["id"]
    })
    return response.json()


def test_list_payments_empty(client):
    response = client.get("/payment/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["limit"] == 100
    assert data["offset"] == 0
    assert data["pages"] == 0


def test_create_payment(client, student):
    payment_data = {
        "amount_in_cents": 10000,
        "status": "completed",
        "payment_method": "card",
        "student_id": student["id"]
    }
    response = client.post("/payment/", json=payment_data)
    assert response.status_code == 201
    data = response.json()
    assert data["amount_in_cents"] == 10000
    assert data["status"] == "completed"
    assert data["payment_method"] == "card"
    assert data["student_id"] == student["id"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_payment_student_not_found(client):
    payment_data = {
        "amount_in_cents": 10000,
        "status": "pending",
        "payment_method": "cash",
        "student_id": 999
    }
    response = client.post("/payment/", json=payment_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"


def test_get_payment(client, student):
    payment_data = {
        "amount_in_cents": 10000,
        "status": "pending",
        "payment_method": "bank_transfer",
        "student_id": student["id"]
    }
    create_response = client.post("/payment/", json=payment_data)
    payment_id = create_response.json()["id"]

    response = client.get(f"/payment/{payment_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == payment_id
    assert data["amount_in_cents"] == 10000


def test_get_payment_not_found(client):
    response = client.get("/payment/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Payment not found"


def test_list_payments_with_data(client, student):
    client.post("/payment/", json={
        "amount_in_cents": 10000,
        "status": "pending",
        "payment_method": "cash",
        "student_id": student["id"]
    })
    client.post("/payment/", json={
        "amount_in_cents": 20000,
        "status": "completed",
        "payment_method": "card",
        "student_id": student["id"]
    })

    response = client.get("/payment/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["pages"] == 1


def test_list_payments_pagination(client, student):
    for i in range(5):
        client.post("/payment/", json={
            "amount_in_cents": 10000 * (i + 1),
            "status": "pending",
            "payment_method": "cash",
            "student_id": student["id"]
        })

    response = client.get("/payment/?limit=2&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert data["pages"] == 3


def test_update_payment(client, student):
    payment_data = {
        "amount_in_cents": 10000,
        "status": "pending",
        "payment_method": "cash",
        "student_id": student["id"]
    }
    create_response = client.post("/payment/", json=payment_data)
    payment_id = create_response.json()["id"]

    update_data = {"status": "completed", "amount_in_cents": 15000}
    response = client.put(f"/payment/{payment_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["amount_in_cents"] == 15000


def test_update_payment_not_found(client):
    response = client.put("/payment/999", json={"status": "completed"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Payment not found"


def test_update_payment_student_not_found(client, student):
    payment_data = {
        "amount_in_cents": 10000,
        "status": "pending",
        "payment_method": "cash",
        "student_id": student["id"]
    }
    create_response = client.post("/payment/", json=payment_data)
    payment_id = create_response.json()["id"]

    response = client.put(f"/payment/{payment_id}", json={"student_id": 999})
    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"


def test_delete_payment(client, student):
    payment_data = {
        "amount_in_cents": 10000,
        "status": "pending",
        "payment_method": "cash",
        "student_id": student["id"]
    }
    create_response = client.post("/payment/", json=payment_data)
    payment_id = create_response.json()["id"]

    response = client.delete(f"/payment/{payment_id}")
    assert response.status_code == 204

    get_response = client.get(f"/payment/{payment_id}")
    assert get_response.status_code == 404


def test_delete_payment_not_found(client):
    response = client.delete("/payment/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Payment not found"
