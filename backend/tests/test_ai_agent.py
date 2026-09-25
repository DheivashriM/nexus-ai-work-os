def test_ai_agent_read_projects(client, seed_users):
    admin = seed_users["admin"]
    client.post("/api/projects", json={"name": "AI Test Project", "owner_id": admin.id})

    response = client.post(
        "/api/ai/chat",
        json={"message": "What projects do we have?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "AI Test Project" in data["reply"] or len(data["execution_steps"]) > 0

def test_ai_agent_create_and_assign_task(client, seed_users):
    admin = seed_users["admin"]
    client.post("/api/projects", json={"name": "Payment Project", "owner_id": admin.id})

    # 1. Create task via AI
    create_resp = client.post(
        "/api/ai/chat",
        json={"message": "Create a high-priority task called Payment API Integration."}
    )
    assert create_resp.status_code == 200
    conv_id = create_resp.json()["conversation_id"]

    # 2. Assign task to Member Test User via AI (multi-turn context test)
    assign_resp = client.post(
        "/api/ai/chat",
        json={"message": "Assign it to Member Test User.", "conversation_id": conv_id}
    )
    assert assign_resp.status_code == 200
    assert "Member Test User" in assign_resp.json()["reply"]

def test_ai_agent_blocker_lifecycle(client, seed_users):
    admin = seed_users["admin"]
    client.post("/api/projects", json={"name": "Blocker AI Project", "owner_id": admin.id})
    client.post("/api/tasks", json={"project_id": admin.id, "title": "Payment API", "status": "TODO"})

    # Report blocker
    block_resp = client.post(
        "/api/ai/chat",
        json={"message": "Mark Payment API blocked because API credentials are missing."}
    )
    assert block_resp.status_code == 200

    # Query blockers
    get_block_resp = client.post(
        "/api/ai/chat",
        json={"message": "What blockers do we have?"}
    )
    assert get_block_resp.status_code == 200
    assert "blocker" in get_block_resp.json()["reply"].lower() or len(get_block_resp.json()["execution_steps"]) > 0

def test_ai_action_logs_auditing(client, seed_users):
    response = client.get("/api/ai/action-logs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_ai_agent_email_and_daily_plan_analysis(client, seed_users):
    # 1. Simulate incoming critical email
    email_resp = client.post(
        "/api/emails/simulate",
        json={
            "sender": "John Acme",
            "sender_email": "john@acme.com",
            "subject": "Production Outage in Payment Gateway",
            "body": "System crash emergency! Critical outage."
        }
    )
    assert email_resp.status_code == 201

    # 2. Query critical emails via AI
    crit_email_chat = client.post(
        "/api/ai/chat",
        json={"message": "what the mails that in critical?"}
    )
    assert crit_email_chat.status_code == 200
    chat_data = crit_email_chat.json()
    assert "reply" in chat_data
    assert "Production Outage" in chat_data["reply"] or "CRITICAL" in chat_data["reply"]

    # 3. Query daily action plan via AI
    daily_plan_chat = client.post(
        "/api/ai/chat",
        json={"message": "what i need to do today?"}
    )
    assert daily_plan_chat.status_code == 200
    plan_data = daily_plan_chat.json()
    assert "Daily Action Plan" in plan_data["reply"] or "CRITICAL" in plan_data["reply"]

def test_natural_language_assign_work_creation(client, seed_users):
    admin = seed_users["admin"]
    client.post("/api/projects", json={"name": "Website for food", "owner_id": admin.id})

    # Test 1: Natural phrasing "Assign Azar to work on the frontend design for website on food project"
    resp1 = client.post(
        "/api/ai/chat",
        json={"message": "Assign Azar to work on the frontend design for website on food project"}
    )
    assert resp1.status_code == 200
    data1 = resp1.json()
    conv_id = data1["conversation_id"]
    assert "frontend design" in data1["reply"].lower() or "azar" in data1["reply"].lower()

    # Test 2: Multi-turn follow-up "assign to work on the backend api"
    resp2 = client.post(
        "/api/ai/chat",
        json={"message": "assign to work on the backend api", "conversation_id": conv_id}
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert "backend api" in data2["reply"].lower() or len(data2["execution_steps"]) > 0

def test_ai_agent_schedule_meeting_tool(client, seed_users):
    resp = client.post(
        "/api/ai/chat",
        json={"message": "Schedule a meeting with Priyan Sharma today at 8pm for Sprint Sync"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "meeting" in data["reply"].lower() or "scheduled" in data["reply"].lower() or len(data["execution_steps"]) > 0

def test_ai_agent_whatsapp_message_tool(client, seed_users):
    resp = client.post(
        "/api/ai/chat",
        json={"message": "Send a WhatsApp message to Sibi saying Please review the PR"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "whatsapp" in data["reply"].lower() or len(data["execution_steps"]) > 0


