def test_get_channels_default(client, seed_users):
    response = client.get("/api/chat/channels")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_create_direct_chat_and_message(client, seed_users):
    admin = seed_users["admin"]
    manager = seed_users["manager"]

    # 1. Create Direct Chat
    resp = client.post(
        "/api/chat/direct",
        json={"recipient_id": manager.id}
    )
    assert resp.status_code == 200
    channel = resp.json()
    assert channel["type"] == "DIRECT"
    ch_id = channel["id"]

    # 2. Send Message
    msg_resp = client.post(
        f"/api/chat/channels/{ch_id}/messages",
        json={"content": "Hello Manager!"}
    )
    assert msg_resp.status_code == 200
    msg = msg_resp.json()
    assert msg["content"] == "Hello Manager!"
    assert msg["channel_id"] == ch_id

    # 3. Get Channel Messages
    msgs_resp = client.get(f"/api/chat/channels/{ch_id}/messages")
    assert msgs_resp.status_code == 200
    msgs = msgs_resp.json()
    assert len(msgs) >= 1
    assert msgs[-1]["content"] == "Hello Manager!"

def test_create_group_channel(client, seed_users):
    admin = seed_users["admin"]
    manager = seed_users["manager"]
    member = seed_users["member"]

    resp = client.post(
        "/api/chat/group",
        json={
            "name": "design-review",
            "description": "Design discussions channel",
            "member_ids": [manager.id, member.id]
        }
    )
    assert resp.status_code == 200
    ch = resp.json()
    assert ch["type"] == "GROUP"
    assert ch["name"] == "design-review"
    assert len(ch["members"]) >= 3
