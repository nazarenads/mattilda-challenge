def test_list_schools_empty(client):
    response = client.get("/school/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["limit"] == 100
    assert data["offset"] == 0
    assert data["pages"] == 0


def test_create_school(client):
    school_data = {
        "name": "Test School",
        "country": "US",
        "tax_id": "123456789"
    }
    response = client.post("/school/", json=school_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test School"
    assert data["country"] == "US"
    assert data["tax_id"] == "123456789"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_get_school(client):
    school_data = {"name": "Test School", "country": "US", "tax_id": "123456789"}
    create_response = client.post("/school/", json=school_data)
    school_id = create_response.json()["id"]

    response = client.get(f"/school/{school_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == school_id
    assert data["name"] == "Test School"


def test_get_school_not_found(client):
    response = client.get("/school/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "School not found"


def test_list_schools_with_data(client):
    client.post("/school/", json={"name": "School 1", "country": "US", "tax_id": "111"})
    client.post("/school/", json={"name": "School 2", "country": "UK", "tax_id": "222"})

    response = client.get("/school/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["pages"] == 1


def test_list_schools_pagination(client):
    for i in range(5):
        client.post("/school/", json={"name": f"School {i}", "country": "US", "tax_id": f"{i}"})

    response = client.get("/school/?limit=2&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert data["pages"] == 3


def test_update_school(client):
    school_data = {"name": "Original Name", "country": "US", "tax_id": "123"}
    create_response = client.post("/school/", json=school_data)
    school_id = create_response.json()["id"]

    update_data = {"name": "Updated Name"}
    response = client.put(f"/school/{school_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["country"] == "US"


def test_update_school_not_found(client):
    response = client.put("/school/999", json={"name": "New Name"})
    assert response.status_code == 404
    assert response.json()["detail"] == "School not found"


def test_delete_school(client):
    school_data = {"name": "To Delete", "country": "US", "tax_id": "123"}
    create_response = client.post("/school/", json=school_data)
    school_id = create_response.json()["id"]

    response = client.delete(f"/school/{school_id}")
    assert response.status_code == 204

    get_response = client.get(f"/school/{school_id}")
    assert get_response.status_code == 404


def test_delete_school_not_found(client):
    response = client.delete("/school/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "School not found"


def test_get_school_balance_empty(client):
    """Test balance for school with no students/invoices."""
    school_data = {"name": "Test School", "country": "US", "tax_id": "123"}
    create_response = client.post("/school/", json=school_data)
    school_id = create_response.json()["id"]

    response = client.get(f"/school/{school_id}/balance")
    assert response.status_code == 200
    data = response.json()
    assert data["total_invoiced_cents"] == 0
    assert data["total_paid_cents"] == 0
    assert data["total_pending_cents"] == 0
    assert data["currency"] is None
    assert data["invoices"] == []
    assert data["payments"] == []


def test_get_school_balance_with_data(client):
    """Test balance with invoices and payments across multiple students."""
    school_response = client.post("/school/", json={"name": "Test School", "country": "US", "tax_id": "123"})
    school_id = school_response.json()["id"]

    student1_response = client.post("/student/", json={
        "identifier": "ID-001",
        "name": "Student 1",
        "email": "s1@example.com",
        "school_id": school_id
    })
    student1_id = student1_response.json()["id"]

    student2_response = client.post("/student/", json={
        "identifier": "ID-002",
        "name": "Student 2",
        "email": "s2@example.com",
        "school_id": school_id
    })
    student2_id = student2_response.json()["id"]

    invoice1_response = client.post("/invoice/", json={
        "invoice_number": "INV-001",
        "amount_in_cents": 10000,
        "currency": "USD",
        "status": "overdue",
        "issue_date": "2024-01-01T00:00:00",
        "due_date": "2024-01-15T00:00:00",
        "student_id": student1_id
    })
    invoice1_id = invoice1_response.json()["id"]

    client.post("/invoice/", json={
        "invoice_number": "INV-002",
        "amount_in_cents": 5000,
        "currency": "USD",
        "status": "pending",
        "issue_date": "2024-01-01T00:00:00",
        "due_date": "2024-02-01T00:00:00",
        "student_id": student2_id
    })

    payment_response = client.post("/payment/", json={
        "amount_in_cents": 4000,
        "status": "completed",
        "payment_method": "card",
        "student_id": student1_id
    })
    payment_id = payment_response.json()["id"]

    client.post("/payment-allocation/", json={
        "payment_id": payment_id,
        "invoice_id": invoice1_id,
        "amount_in_cents": 4000
    })

    response = client.get(f"/school/{school_id}/balance")
    assert response.status_code == 200
    data = response.json()
    assert data["total_invoiced_cents"] == 15000
    assert data["total_paid_cents"] == 4000
    assert data["total_pending_cents"] == 11000
    assert data["currency"] == "USD"
    assert len(data["invoices"]) == 2
    assert len(data["payments"]) == 1


def test_get_school_balance_not_found(client):
    response = client.get("/school/999/balance")
    assert response.status_code == 404
    assert response.json()["detail"] == "School not found"
