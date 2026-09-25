def test_create_and_assign_task(client, seed_users):
    admin = seed_users["admin"]
    member = seed_users["member"]

    # 1. Create project
    proj_resp = client.post(
        "/api/projects",
        json={
            "name": "Task Test Project",
            "owner_id": admin.id
        }
    )
    project_id = proj_resp.json()["id"]

    # 2. Create task
    task_resp = client.post(
        "/api/tasks",
        json={
            "project_id": project_id,
            "title": "Build Authentication Middleware",
            "description": "Implement JWT verification",
            "status": "TODO",
            "priority": "HIGH",
            "assignee_id": member.id
        }
    )
    assert task_resp.status_code == 201
    task = task_resp.json()
    assert task["title"] == "Build Authentication Middleware"
    assert task["assignee_id"] == member.id

    # 3. Update task status
    update_resp = client.put(
        f"/api/tasks/{task['id']}",
        json={"status": "IN_PROGRESS"}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "IN_PROGRESS"

def test_create_task_invalid_project(client, seed_users):
    member = seed_users["member"]
    response = client.post(
        "/api/tasks",
        json={
            "project_id": "invalid-project-id",
            "title": "Orphaned Task",
            "assignee_id": member.id
        }
    )
    assert response.status_code == 404
    assert "Project" in response.json()["detail"]
