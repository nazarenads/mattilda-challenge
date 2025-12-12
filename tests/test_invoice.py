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


def test_list_invoices_empty(client):
    response = client.get("/invoice/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["limit"] == 100
    assert data["offset"] == 0
    assert data["pages"] == 0


def test_create_invoice(client, student):
    invoice_data = {
        "invoice_number": "INV-001",
        "amount_in_cents": 10050,
        "currency": "USD",
        "status": "pending",
        "issue_date": "2024-01-01T00:00:00",
        "due_date": "2024-02-01T00:00:00",
        "description": "Monthly fee",
        "student_id": student["id"]
    }
    response = client.post("/invoice/", json=invoice_data)
    assert response.status_code == 201
    data = response.json()
    assert data["invoice_number"] == "INV-001"
    assert data["amount_in_cents"] == 10050
    assert data["currency"] == "USD"
    assert data["status"] == "pending"
    assert data["student_id"] == student["id"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_invoice_student_not_found(client):
    invoice_data = {
        "invoice_number": "INV-001",
        "amount_in_cents": 10050,
        "currency": "USD",
        "status": "pending",
        "issue_date": "2024-01-01T00:00:00",
        "due_date": "2024-02-01T00:00:00",
        "student_id": 999
    }
    response = client.post("/invoice/", json=invoice_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"


def test_get_invoice(client, student):
    invoice_data = {
        "invoice_number": "INV-001",
        "amount_in_cents": 10050,
        "currency": "USD",
        "issue_date": "2024-01-01T00:00:00",
        "due_date": "2024-02-01T00:00:00",
        "student_id": student["id"]
    }
    create_response = client.post("/invoice/", json=invoice_data)
    invoice_id = create_response.json()["id"]

    response = client.get(f"/invoice/{invoice_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == invoice_id
    assert data["invoice_number"] == "INV-001"


def test_get_invoice_not_found(client):
    response = client.get("/invoice/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Invoice not found"


def test_list_invoices_with_data(client, student):
    client.post("/invoice/", json={
        "invoice_number": "INV-001",
        "amount_in_cents": 10000,
        "currency": "USD",
        "issue_date": "2024-01-01T00:00:00",
        "due_date": "2024-02-01T00:00:00",
        "student_id": student["id"]
    })
    client.post("/invoice/", json={
        "invoice_number": "INV-002",
        "amount_in_cents": 20000,
        "currency": "USD",
        "issue_date": "2024-01-01T00:00:00",
        "due_date": "2024-02-01T00:00:00",
        "student_id": student["id"]
    })

    response = client.get("/invoice/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["pages"] == 1


def test_list_invoices_pagination(client, student):
    for i in range(5):
        client.post("/invoice/", json={
            "invoice_number": f"INV-00{i}",
            "amount_in_cents": 10000 * i,
            "currency": "USD",
            "issue_date": "2024-01-01T00:00:00",
            "due_date": "2024-02-01T00:00:00",
            "student_id": student["id"]
        })

    response = client.get("/invoice/?limit=2&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert data["pages"] == 3


def test_update_invoice(client, student):
    invoice_data = {
        "invoice_number": "INV-001",
        "amount_in_cents": 10000,
        "currency": "USD",
        "status": "pending",
        "issue_date": "2024-01-01T00:00:00",
        "due_date": "2024-02-01T00:00:00",
        "student_id": student["id"]
    }
    create_response = client.post("/invoice/", json=invoice_data)
    invoice_id = create_response.json()["id"]

    update_data = {"status": "paid", "amount_in_cents": 15000}
    response = client.put(f"/invoice/{invoice_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "paid"
    assert data["amount_in_cents"] == 15000
    assert data["invoice_number"] == "INV-001"


def test_update_invoice_not_found(client):
    response = client.put("/invoice/999", json={"status": "paid"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Invoice not found"


def test_update_invoice_student_not_found(client, student):
    invoice_data = {
        "invoice_number": "INV-001",
        "amount_in_cents": 10000,
        "currency": "USD",
        "issue_date": "2024-01-01T00:00:00",
        "due_date": "2024-02-01T00:00:00",
        "student_id": student["id"]
    }
    create_response = client.post("/invoice/", json=invoice_data)
    invoice_id = create_response.json()["id"]

    response = client.put(f"/invoice/{invoice_id}", json={"student_id": 999})
    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"


def test_delete_invoice(client, student):
    invoice_data = {
        "invoice_number": "INV-001",
        "amount_in_cents": 10000,
        "currency": "USD",
        "issue_date": "2024-01-01T00:00:00",
        "due_date": "2024-02-01T00:00:00",
        "student_id": student["id"]
    }
    create_response = client.post("/invoice/", json=invoice_data)
    invoice_id = create_response.json()["id"]

    response = client.delete(f"/invoice/{invoice_id}")
    assert response.status_code == 204

    get_response = client.get(f"/invoice/{invoice_id}")
    assert get_response.status_code == 404


def test_delete_invoice_not_found(client):
    response = client.delete("/invoice/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Invoice not found"
