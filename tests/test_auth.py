class TestLogin:
    def test_login_success(self, client, db_helpers):
        db_helpers.create_user(email="test@example.com", password="testpass123")

        response = client.post(
            "/token",
            data={"username": "test@example.com", "password": "testpass123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, db_helpers):
        db_helpers.create_user(email="test@example.com", password="testpass123")

        response = client.post(
            "/token",
            data={"username": "test@example.com", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"

    def test_login_nonexistent_user(self, client):
        response = client.post(
            "/token",
            data={"username": "nonexistent@example.com", "password": "anypass"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"

    def test_login_admin_user(self, client, db_helpers):
        db_helpers.create_admin_user(email="admin@test.com", password="adminpass")

        response = client.post(
            "/token",
            data={"username": "admin@test.com", "password": "adminpass"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data


class TestAuthenticatedEndpoints:
    def test_unauthenticated_request_rejected(self, client):
        response = client.get("/school/")

        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_invalid_token_rejected(self, client):
        response = client.get(
            "/school/",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"

    def test_authenticated_request_succeeds(self, client, db_helpers, admin_headers):
        response = client.get("/school/", headers=admin_headers)

        assert response.status_code == 200


class TestSchoolUserAccess:
    def test_school_user_can_access_own_school(self, client, school_user_headers, school_user):
        _, school = school_user

        response = client.get(f"/school/{school.id}", headers=school_user_headers)

        assert response.status_code == 200
        assert response.json()["id"] == school.id

    def test_school_user_cannot_access_other_school(self, client, db_helpers, school_user_headers):
        """
        When a school user tries to access another school, they get 404 (not 403)
        to prevent information leakage about which schools exist.
        """
        other_school = db_helpers.create_school(name="Other School", tax_id="999")

        response = client.get(f"/school/{other_school.id}", headers=school_user_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "School not found"

    def test_admin_can_access_any_school(self, client, db_helpers, admin_headers):
        school1 = db_helpers.create_school(name="School 1", tax_id="111")
        school2 = db_helpers.create_school(name="School 2", tax_id="222")

        response1 = client.get(f"/school/{school1.id}", headers=admin_headers)
        response2 = client.get(f"/school/{school2.id}", headers=admin_headers)

        assert response1.status_code == 200
        assert response2.status_code == 200

    def test_school_user_cannot_create_school(self, client, school_user_headers):
        response = client.post(
            "/school/",
            json={"name": "New School", "country": "US", "tax_id": "123"},
            headers=school_user_headers,
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Admin access required"

    def test_admin_can_create_school(self, client, admin_headers):
        response = client.post(
            "/school/",
            json={"name": "New School", "country": "US", "tax_id": "123"},
            headers=admin_headers,
        )

        assert response.status_code == 201

