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


@pytest.fixture
def invoice(client, student):
    response = client.post("/invoice/", json={
        "invoice_number": "INV-001",
        "amount_in_cents": 10000,
        "currency": "USD",
        "status": "pending",
        "issue_date": "2024-01-01T00:00:00",
        "due_date": "2024-02-01T00:00:00",
        "student_id": student["id"]
    })
    return response.json()


@pytest.fixture
def payment(client, student):
    response = client.post("/payment/", json={
        "amount_in_cents": 10000,
        "status": "completed",
        "payment_method": "card",
        "student_id": student["id"]
    })
    return response.json()


def test_list_allocations_empty(client):
    response = client.get("/payment-allocation/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_create_allocation(client, payment, invoice):
    allocation_data = {
        "payment_id": payment["id"],
        "invoice_id": invoice["id"],
        "amount_in_cents": 5000
    }
    response = client.post("/payment-allocation/", json=allocation_data)
    assert response.status_code == 201
    data = response.json()
    assert data["payment_id"] == payment["id"]
    assert data["invoice_id"] == invoice["id"]
    assert data["amount_in_cents"] == 5000
    assert "id" in data
    assert "created_at" in data


def test_create_allocation_payment_not_found(client, invoice):
    allocation_data = {
        "payment_id": 999,
        "invoice_id": invoice["id"],
        "amount_in_cents": 5000
    }
    response = client.post("/payment-allocation/", json=allocation_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Payment not found"


def test_create_allocation_invoice_not_found(client, payment):
    allocation_data = {
        "payment_id": payment["id"],
        "invoice_id": 999,
        "amount_in_cents": 5000
    }
    response = client.post("/payment-allocation/", json=allocation_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Invoice not found"


def test_get_allocation(client, payment, invoice):
    allocation_data = {
        "payment_id": payment["id"],
        "invoice_id": invoice["id"],
        "amount_in_cents": 5000
    }
    create_response = client.post("/payment-allocation/", json=allocation_data)
    allocation_id = create_response.json()["id"]

    response = client.get(f"/payment-allocation/{allocation_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == allocation_id


def test_get_allocation_not_found(client):
    response = client.get("/payment-allocation/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Payment allocation not found"


def test_update_allocation(client, payment, invoice):
    allocation_data = {
        "payment_id": payment["id"],
        "invoice_id": invoice["id"],
        "amount_in_cents": 5000
    }
    create_response = client.post("/payment-allocation/", json=allocation_data)
    allocation_id = create_response.json()["id"]

    update_data = {"amount_in_cents": 7000}
    response = client.put(f"/payment-allocation/{allocation_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["amount_in_cents"] == 7000


def test_update_allocation_not_found(client):
    response = client.put("/payment-allocation/999", json={"amount_in_cents": 5000})
    assert response.status_code == 404
    assert response.json()["detail"] == "Payment allocation not found"


def test_delete_allocation(client, payment, invoice):
    allocation_data = {
        "payment_id": payment["id"],
        "invoice_id": invoice["id"],
        "amount_in_cents": 5000
    }
    create_response = client.post("/payment-allocation/", json=allocation_data)
    allocation_id = create_response.json()["id"]

    response = client.delete(f"/payment-allocation/{allocation_id}")
    assert response.status_code == 204

    get_response = client.get(f"/payment-allocation/{allocation_id}")
    assert get_response.status_code == 404


def test_delete_allocation_not_found(client):
    response = client.delete("/payment-allocation/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Payment allocation not found"


def test_allocation_updates_invoice_status_to_partially_paid(client, student):
    """When allocation is less than invoice amount, status becomes partially_paid."""
    invoice_response = client.post("/invoice/", json={
        "invoice_number": "INV-002",
        "amount_in_cents": 10000,
        "currency": "USD",
        "status": "pending",
        "issue_date": "2024-01-01T00:00:00",
        "due_date": "2024-02-01T00:00:00",
        "student_id": student["id"]
    })
    invoice = invoice_response.json()

    payment_response = client.post("/payment/", json={
        "amount_in_cents": 5000,
        "status": "completed",
        "payment_method": "card",
        "student_id": student["id"]
    })
    payment = payment_response.json()

    client.post("/payment-allocation/", json={
        "payment_id": payment["id"],
        "invoice_id": invoice["id"],
        "amount_in_cents": 5000
    })

    invoice_check = client.get(f"/invoice/{invoice['id']}")
    assert invoice_check.json()["status"] == "partially_paid"


def test_allocation_updates_invoice_status_to_paid(client, student):
    """When total allocations >= invoice amount, status becomes paid."""
    invoice_response = client.post("/invoice/", json={
        "invoice_number": "INV-003",
        "amount_in_cents": 10000,
        "currency": "USD",
        "status": "pending",
        "issue_date": "2024-01-01T00:00:00",
        "due_date": "2024-02-01T00:00:00",
        "student_id": student["id"]
    })
    invoice = invoice_response.json()

    payment_response = client.post("/payment/", json={
        "amount_in_cents": 10000,
        "status": "completed",
        "payment_method": "card",
        "student_id": student["id"]
    })
    payment = payment_response.json()

    client.post("/payment-allocation/", json={
        "payment_id": payment["id"],
        "invoice_id": invoice["id"],
        "amount_in_cents": 10000
    })

    invoice_check = client.get(f"/invoice/{invoice['id']}")
    assert invoice_check.json()["status"] == "paid"


def test_multiple_allocations_sum_to_paid(client, student):
    """Multiple allocations from different payments sum up to mark invoice as paid."""
    invoice_response = client.post("/invoice/", json={
        "invoice_number": "INV-004",
        "amount_in_cents": 10000,
        "currency": "USD",
        "status": "pending",
        "issue_date": "2024-01-01T00:00:00",
        "due_date": "2024-02-01T00:00:00",
        "student_id": student["id"]
    })
    invoice = invoice_response.json()

    payment1_response = client.post("/payment/", json={
        "amount_in_cents": 5000,
        "status": "completed",
        "payment_method": "card",
        "student_id": student["id"]
    })
    payment1 = payment1_response.json()

    payment2_response = client.post("/payment/", json={
        "amount_in_cents": 5000,
        "status": "completed",
        "payment_method": "cash",
        "student_id": student["id"]
    })
    payment2 = payment2_response.json()

    client.post("/payment-allocation/", json={
        "payment_id": payment1["id"],
        "invoice_id": invoice["id"],
        "amount_in_cents": 5000
    })

    invoice_check = client.get(f"/invoice/{invoice['id']}")
    assert invoice_check.json()["status"] == "partially_paid"

    client.post("/payment-allocation/", json={
        "payment_id": payment2["id"],
        "invoice_id": invoice["id"],
        "amount_in_cents": 5000
    })

    invoice_check = client.get(f"/invoice/{invoice['id']}")
    assert invoice_check.json()["status"] == "paid"


def test_pending_payment_not_counted_for_invoice_status(client, student):
    """Only completed payments are counted for invoice status calculation."""
    invoice_response = client.post("/invoice/", json={
        "invoice_number": "INV-005",
        "amount_in_cents": 10000,
        "currency": "USD",
        "status": "pending",
        "issue_date": "2024-01-01T00:00:00",
        "due_date": "2024-02-01T00:00:00",
        "student_id": student["id"]
    })
    invoice = invoice_response.json()

    payment_response = client.post("/payment/", json={
        "amount_in_cents": 10000,
        "status": "pending",
        "payment_method": "card",
        "student_id": student["id"]
    })
    payment = payment_response.json()

    client.post("/payment-allocation/", json={
        "payment_id": payment["id"],
        "invoice_id": invoice["id"],
        "amount_in_cents": 10000
    })

    invoice_check = client.get(f"/invoice/{invoice['id']}")
    assert invoice_check.json()["status"] == "pending"
