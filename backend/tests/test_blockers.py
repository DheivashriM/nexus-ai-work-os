def test_blocker_lifecycle(client, seed_users):
    admin = seed_users["admin"]
    member = seed_users["member"]

    proj_resp = client.post("/api/projects", json={"name": "Blocker Project", "owner_id": admin.id})
    project_id = proj_resp.json()["id"]

    task_resp = client.post(
        "/api/tasks",
        json={"project_id": project_id, "title": "Stripe Integration", "assignee_id": member.id}
    )
    task_id = task_resp.json()["id"]

    # File blocker
    blocker_resp = client.post(
        "/api/blockers",
        json={
            "task_id": task_id,
            "description": "Missing API Key",
            "severity": "CRITICAL"
        }
    )
    assert blocker_resp.status_code == 201
    blocker = blocker_resp.json()
    assert blocker["status"] == "OPEN"

    # Verify task auto-marked BLOCKED
    updated_task = client.get(f"/api/tasks/{task_id}").json()
    assert updated_task["status"] == "BLOCKED"

    # Resolve blocker
    res_resp = client.put(f"/api/blockers/{blocker['id']}", json={"status": "RESOLVED"})
    assert res_resp.status_code == 200
    assert res_resp.json()["status"] == "RESOLVED"
