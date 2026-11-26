import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")


def _register(client, email, password):
    return client.post("/register", json={"email": email, "password": password})


def _login(client, email, password):
    return client.post("/login", json={"email": email, "password": password})


def test_register_and_login(client):
    r = _register(client, "user@example.com", "password123")
    assert r.status_code == 200
    assert r.json()["email"] == "user@example.com"
    assert "hashed_password" not in r.json()

    r = _login(client, "user@example.com", "password123")
    assert r.status_code == 200
    assert "access_token" in r.json()

    # wrong password
    r = _login(client, "user@example.com", "wrong")
    assert r.status_code == 401


def test_unauthenticated_protected(client):
    r = client.get("/conversations")
    assert r.status_code == 401


def test_private_data_protection(client):
    _register(client, "a@example.com", "password123")
    _register(client, "b@example.com", "password123")

    token_a = _login(client, "a@example.com", "password123").json()["access_token"]
    token_b = _login(client, "b@example.com", "password123").json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B creates a conversation
    conv = client.post("/conversations", json={"title": "B's private chat"}, headers=headers_b).json()
    conv_id = conv["id"]

    # User A cannot read it
    r = client.get(f"/conversations/{conv_id}", headers=headers_a)
    assert r.status_code == 404

    # User A cannot add a message to it
    r = client.post(f"/conversations/{conv_id}/messages", json={"content": "intrusion"}, headers=headers_a)
    assert r.status_code == 404

    # User B can read and add messages
    r = client.get(f"/conversations/{conv_id}", headers=headers_b)
    assert r.status_code == 200

    r = client.post(f"/conversations/{conv_id}/messages", json={"content": "hello"}, headers=headers_b)
    assert r.status_code == 200
    body = r.json()
    assert body["user_message"]["role"] == "user"
    assert body["assistant_message"]["role"] == "assistant"
    assert body["user_message"]["content"] == "hello"

    # Both messages persisted
    conv2 = client.get(f"/conversations/{conv_id}", headers=headers_b).json()
    assert len(conv2["messages"]) == 2
    roles = [m["role"] for m in conv2["messages"]]
    assert roles == ["user", "assistant"]

    # User A's conversation list does not include B's conversation
    r = client.get("/conversations", headers=headers_a)
    assert r.status_code == 200
    assert all(c["id"] != conv_id for c in r.json())


def test_cache_demo(client):
    r1 = client.get("/cache/demo?q=hello")
    r2 = client.get("/cache/demo?q=hello")
    assert r1.status_code == 200
    assert r2.json()["cached"] is True
