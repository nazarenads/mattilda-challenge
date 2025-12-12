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
