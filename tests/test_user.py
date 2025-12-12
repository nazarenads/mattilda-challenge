class TestUserList:
    def test_list_users_as_admin(self, client, db_helpers, admin_headers):
        db_helpers.create_user(email="user1@example.com")
        db_helpers.create_user(email="user2@example.com")

        response = client.get("/user/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2
        assert len(data["items"]) >= 2

    def test_list_users_as_non_admin_forbidden(self, client, school_user_headers):
        response = client.get("/user/", headers=school_user_headers)

        assert response.status_code == 403
        assert response.json()["detail"] == "Admin access required"


class TestUserCreate:
    def test_create_user_as_admin(self, client, db_helpers, admin_headers):
        school = db_helpers.create_school()

        response = client.post(
            "/user/",
            json={
                "email": "newuser@example.com",
                "password": "password123",
                "school_id": school.id,
                "is_admin": False,
            },
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["school_id"] == school.id
        assert data["is_admin"] is False
        assert "id" in data
        assert "hashed_password" not in data

    def test_create_admin_user(self, client, admin_headers):
        response = client.post(
            "/user/",
            json={
                "email": "newadmin@example.com",
                "password": "adminpass",
                "is_admin": True,
            },
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newadmin@example.com"
        assert data["is_admin"] is True
        assert data["school_id"] is None

    def test_create_user_duplicate_email(self, client, db_helpers, admin_headers):
        db_helpers.create_user(email="existing@example.com")

        response = client.post(
            "/user/",
            json={
                "email": "existing@example.com",
                "password": "password123",
            },
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"

    def test_create_user_school_not_found(self, client, admin_headers):
        response = client.post(
            "/user/",
            json={
                "email": "newuser@example.com",
                "password": "password123",
                "school_id": 999,
            },
            headers=admin_headers,
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "School not found"

    def test_create_user_as_non_admin_forbidden(self, client, school_user_headers):
        response = client.post(
            "/user/",
            json={
                "email": "newuser@example.com",
                "password": "password123",
            },
            headers=school_user_headers,
        )

        assert response.status_code == 403


class TestUserGet:
    def test_get_user_as_admin(self, client, db_helpers, admin_headers):
        user = db_helpers.create_user(email="testuser@example.com")

        response = client.get(f"/user/{user.id}", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user.id
        assert data["email"] == "testuser@example.com"

    def test_get_user_not_found(self, client, admin_headers):
        response = client.get("/user/999", headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    def test_get_user_as_non_admin_forbidden(self, client, db_helpers, school_user_headers):
        user = db_helpers.create_user(email="other@example.com")

        response = client.get(f"/user/{user.id}", headers=school_user_headers)

        assert response.status_code == 403


class TestUserUpdate:
    def test_update_user_as_admin(self, client, db_helpers, admin_headers):
        user = db_helpers.create_user(email="old@example.com")

        response = client.put(
            f"/user/{user.id}",
            json={"email": "new@example.com"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "new@example.com"

    def test_update_user_password(self, client, db_helpers, admin_headers):
        user = db_helpers.create_user(email="user@example.com", password="oldpass")

        response = client.put(
            f"/user/{user.id}",
            json={"password": "newpass123"},
            headers=admin_headers,
        )

        assert response.status_code == 200

        login_response = client.post(
            "/token",
            data={"username": "user@example.com", "password": "newpass123"},
        )
        assert login_response.status_code == 200

    def test_update_user_not_found(self, client, admin_headers):
        response = client.put(
            "/user/999",
            json={"email": "new@example.com"},
            headers=admin_headers,
        )

        assert response.status_code == 404

    def test_update_user_duplicate_email(self, client, db_helpers, admin_headers):
        db_helpers.create_user(email="existing@example.com")
        user = db_helpers.create_user(email="user@example.com")

        response = client.put(
            f"/user/{user.id}",
            json={"email": "existing@example.com"},
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"


class TestUserDelete:
    def test_delete_user_as_admin(self, client, db_helpers, admin_headers):
        user = db_helpers.create_user(email="todelete@example.com")
        user_id = user.id

        response = client.delete(f"/user/{user_id}", headers=admin_headers)

        assert response.status_code == 204
        assert db_helpers.get_user(user_id) is None

    def test_delete_user_not_found(self, client, admin_headers):
        response = client.delete("/user/999", headers=admin_headers)

        assert response.status_code == 404

    def test_delete_user_as_non_admin_forbidden(self, client, db_helpers, school_user_headers):
        user = db_helpers.create_user(email="other@example.com")

        response = client.delete(f"/user/{user.id}", headers=school_user_headers)

        assert response.status_code == 403

