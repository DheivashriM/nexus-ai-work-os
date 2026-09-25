def test_create_user(client):
    response = client.post(
        "/api/users",
        json={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "password": "secretpassword",
            "role": "MEMBER",
            "status": "ACTIVE"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Jane Doe"
    assert data["email"] == "jane@example.com"
    assert "password_hash" not in data

def test_duplicate_user_email(client, seed_users):
    response = client.post(
        "/api/users",
        json={
            "name": "Duplicate Admin",
            "email": "admin@test.com",
            "password": "secretpassword",
            "role": "MEMBER"
        }
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_get_users(client, seed_users):
    response = client.get("/api/users")
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 3
