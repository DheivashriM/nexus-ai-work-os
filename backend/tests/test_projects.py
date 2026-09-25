def test_create_project(client, seed_users):
    admin = seed_users["admin"]
    response = client.post(
        "/api/projects",
        json={
            "name": "Project Alpha",
            "description": "Test project description",
            "status": "ACTIVE",
            "priority": "HIGH",
            "owner_id": admin.id
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Project Alpha"
    assert data["owner_id"] == admin.id

def test_create_project_invalid_owner(client):
    response = client.post(
        "/api/projects",
        json={
            "name": "Project Invalid",
            "description": "Invalid owner test",
            "status": "ACTIVE",
            "priority": "MEDIUM",
            "owner_id": "nonexistent-uuid-1234"
        }
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
