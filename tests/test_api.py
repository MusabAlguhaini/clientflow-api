from datetime import date, timedelta

from tests.conftest import register_and_login


def test_register_login_me(client):
    res = client.post("/auth/register", json={"email": "Bob@Example.com", "full_name": "Bob", "password": "password123"})
    assert res.status_code == 201
    assert res.json()["email"] == "bob@example.com"
    assert "password" not in res.json()

    token = client.post("/auth/login", data={"username": "bob@example.com", "password": "password123"}).json()
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token['access_token']}"})
    assert me.status_code == 200 and me.json()["full_name"] == "Bob"


def test_duplicate_email_and_bad_password(client):
    payload = {"email": "a@b.co", "full_name": "A", "password": "password123"}
    assert client.post("/auth/register", json=payload).status_code == 201
    assert client.post("/auth/register", json=payload).status_code == 409
    bad = client.post("/auth/login", data={"username": "a@b.co", "password": "wrong-password"})
    assert bad.status_code == 401


def test_requires_auth(client):
    assert client.get("/clients").status_code == 401
    assert client.get("/tasks").status_code == 401


def test_client_crud_and_search(client, auth):
    created = client.post("/clients", json={"name": "Acme Corp", "company": "Acme"}, headers=auth)
    assert created.status_code == 201
    cid = created.json()["id"]
    client.post("/clients", json={"name": "Globex"}, headers=auth)

    assert len(client.get("/clients", headers=auth).json()) == 2
    found = client.get("/clients", params={"q": "acme"}, headers=auth).json()
    assert [c["id"] for c in found] == [cid]

    patched = client.patch(f"/clients/{cid}", json={"notes": "VIP"}, headers=auth)
    assert patched.json()["notes"] == "VIP" and patched.json()["name"] == "Acme Corp"

    assert client.delete(f"/clients/{cid}", headers=auth).status_code == 204
    assert client.get(f"/clients/{cid}", headers=auth).status_code == 404


def test_users_cannot_see_each_others_data(client, auth):
    cid = client.post("/clients", json={"name": "Private"}, headers=auth).json()["id"]
    tid = client.post(f"/clients/{cid}/tasks", json={"title": "Secret"}, headers=auth).json()["id"]

    other = register_and_login(client, "eve@example.com")
    assert client.get(f"/clients/{cid}", headers=other).status_code == 404
    assert client.get(f"/tasks/{tid}", headers=other).status_code == 404
    assert client.post(f"/clients/{cid}/tasks", json={"title": "x"}, headers=other).status_code == 404
    assert client.get("/clients", headers=other).json() == []
    assert client.get("/tasks", headers=other).json() == []


def test_task_lifecycle_and_filters(client, auth):
    cid = client.post("/clients", json={"name": "Acme"}, headers=auth).json()["id"]
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    t1 = client.post(
        f"/clients/{cid}/tasks", json={"title": "Late", "priority": "high", "due_date": yesterday}, headers=auth
    ).json()
    client.post(f"/clients/{cid}/tasks", json={"title": "Fresh"}, headers=auth)

    assert len(client.get("/tasks", headers=auth).json()) == 2
    assert [t["id"] for t in client.get("/tasks", params={"overdue": True}, headers=auth).json()] == [t1["id"]]
    assert len(client.get("/tasks", params={"priority": "high"}, headers=auth).json()) == 1

    done = client.patch(f"/tasks/{t1['id']}", json={"status": "done"}, headers=auth)
    assert done.json()["status"] == "done"
    assert client.get("/tasks", params={"overdue": True}, headers=auth).json() == []
    assert len(client.get("/tasks", params={"status": "done"}, headers=auth).json()) == 1


def test_summary(client, auth):
    cid = client.post("/clients", json={"name": "Acme"}, headers=auth).json()["id"]
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    client.post(f"/clients/{cid}/tasks", json={"title": "A", "due_date": yesterday}, headers=auth)
    t = client.post(f"/clients/{cid}/tasks", json={"title": "B"}, headers=auth).json()
    client.patch(f"/tasks/{t['id']}", json={"status": "in_progress"}, headers=auth)

    s = client.get("/tasks/summary", headers=auth).json()
    assert s["clients"] == 1 and s["tasks_total"] == 2 and s["overdue_tasks"] == 1
    assert s["tasks_by_status"] == {"todo": 1, "in_progress": 1, "done": 0}


def test_validation_errors(client, auth):
    assert client.post("/auth/register", json={"email": "nope", "full_name": "x", "password": "password123"}).status_code == 422
    assert client.post("/clients", json={"name": ""}, headers=auth).status_code == 422
    cid = client.post("/clients", json={"name": "Acme"}, headers=auth).json()["id"]
    assert client.post(f"/clients/{cid}/tasks", json={"title": "x", "status": "bogus"}, headers=auth).status_code == 422


def test_deleting_client_cascades_tasks(client, auth):
    cid = client.post("/clients", json={"name": "Acme"}, headers=auth).json()["id"]
    tid = client.post(f"/clients/{cid}/tasks", json={"title": "T"}, headers=auth).json()["id"]
    client.delete(f"/clients/{cid}", headers=auth)
    assert client.get(f"/tasks/{tid}", headers=auth).status_code == 404
