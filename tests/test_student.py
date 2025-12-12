import pytest


@pytest.fixture
def school(client):
    response = client.post("/school/", json={
        "name": "Test School",
        "country": "US",
        "tax_id": "123456789"
    })
    return response.json()


def test_list_students_empty(client):
    response = client.get("/student/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["limit"] == 100
    assert data["offset"] == 0
    assert data["pages"] == 0


def test_create_student(client, school):
    student_data = {
        "identifier": "ID-001",
        "name": "John Doe",
        "email": "john@example.com",
        "school_id": school["id"]
    }
    response = client.post("/student/", json=student_data)
    assert response.status_code == 201
    data = response.json()
    assert data["identifier"] == "ID-001"
    assert data["name"] == "John Doe"
    assert data["email"] == "john@example.com"
    assert data["school_id"] == school["id"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_student_school_not_found(client):
    student_data = {
        "identifier": "ID-001",
        "name": "John Doe",
        "email": "john@example.com",
        "school_id": 999
    }
    response = client.post("/student/", json=student_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "School not found"


def test_get_student(client, school):
    student_data = {"identifier": "ID-001", "name": "John Doe", "email": "john@example.com", "school_id": school["id"]}
    create_response = client.post("/student/", json=student_data)
    student_id = create_response.json()["id"]

    response = client.get(f"/student/{student_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == student_id
    assert data["name"] == "John Doe"


def test_get_student_not_found(client):
    response = client.get("/student/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"


def test_list_students_with_data(client, school):
    client.post("/student/", json={"identifier": "ID-001", "name": "Student 1", "email": "s1@example.com", "school_id": school["id"]})
    client.post("/student/", json={"identifier": "ID-002", "name": "Student 2", "email": "s2@example.com", "school_id": school["id"]})

    response = client.get("/student/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["pages"] == 1


def test_list_students_pagination(client, school):
    for i in range(5):
        client.post("/student/", json={"identifier": f"ID-{i}", "name": f"Student {i}", "email": f"s{i}@example.com", "school_id": school["id"]})

    response = client.get("/student/?limit=2&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert data["pages"] == 3


def test_update_student(client, school):
    student_data = {"identifier": "ID-001", "name": "Original Name", "email": "original@example.com", "school_id": school["id"]}
    create_response = client.post("/student/", json=student_data)
    student_id = create_response.json()["id"]

    update_data = {"name": "Updated Name"}
    response = client.put(f"/student/{student_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["email"] == "original@example.com"


def test_update_student_not_found(client):
    response = client.put("/student/999", json={"name": "New Name"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"


def test_update_student_school_not_found(client, school):
    student_data = {"identifier": "ID-001", "name": "Test", "email": "test@example.com", "school_id": school["id"]}
    create_response = client.post("/student/", json=student_data)
    student_id = create_response.json()["id"]

    response = client.put(f"/student/{student_id}", json={"school_id": 999})
    assert response.status_code == 404
    assert response.json()["detail"] == "School not found"


def test_delete_student(client, school):
    student_data = {"identifier": "ID-001", "name": "To Delete", "email": "delete@example.com", "school_id": school["id"]}
    create_response = client.post("/student/", json=student_data)
    student_id = create_response.json()["id"]

    response = client.delete(f"/student/{student_id}")
    assert response.status_code == 204

    get_response = client.get(f"/student/{student_id}")
    assert get_response.status_code == 404


def test_delete_student_not_found(client):
    response = client.delete("/student/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"
