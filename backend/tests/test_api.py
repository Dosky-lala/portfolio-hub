import pytest


def make(client, chapter=1, **extra):
    """Helper: create a project and return the response."""
    payload = {"chapter": chapter, "title": f"Chapter {chapter}", **extra}
    return client.post("/api/projects", json=payload)


def test_health_reports_db_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "db": "ok"}


def test_create_project_applies_default_gate(client):
    r = make(client, repo_url="https://github.com/Dosky-lala/portfolio-hub")
    assert r.status_code == 201
    body = r.json()
    assert body["chapter"] == 1
    assert body["repo_url"] == "https://github.com/Dosky-lala/portfolio-hub"
    assert body["gate"]["runs_verified"] is False
    assert body["gate"]["gitops_working"] is None  # N/A until Chapter 4


def test_duplicate_chapter_returns_409(client):
    assert make(client).status_code == 201
    assert make(client).status_code == 409


@pytest.mark.parametrize("payload", [
    {"chapter": 0, "title": "x"},                           # chapter must be >= 1
    {"chapter": 1, "title": ""},                            # title can't be empty
    {"chapter": 1, "title": "x", "repo_url": "not-a-url"},  # must be a real URL
])
def test_invalid_create_returns_422(client, payload):
    assert client.post("/api/projects", json=payload).status_code == 422


def test_patch_gate_changes_only_the_sent_box(client):
    pid = make(client).json()["id"]
    r = client.patch(f"/api/projects/{pid}", json={"gate": {"runs_verified": True}})
    assert r.status_code == 200
    gate = r.json()["gate"]
    assert gate["runs_verified"] is True
    assert gate["cicd_working"] is False      # untouched boxes keep their values
    assert gate["gitops_working"] is None
    # Re-read in a NEW request: proves the change was SAVED, not just echoed back
    assert client.get(f"/api/projects/{pid}").json()["gate"]["runs_verified"] is True


@pytest.mark.parametrize("payload", [
    {"gate": {"runs_verfied": True}},  # typo in a gate key
    {"chapter": 2},                    # chapter can't be changed after creation
    {"title": None},                   # explicit null title
])
def test_invalid_patch_returns_422(client, payload):
    pid = make(client).json()["id"]
    assert client.patch(f"/api/projects/{pid}", json=payload).status_code == 422


def test_missing_project_returns_404(client):
    assert client.get("/api/projects/999").status_code == 404
    assert client.patch("/api/projects/999", json={"title": "x"}).status_code == 404
    assert client.delete("/api/projects/999").status_code == 404


def test_delete_then_gone(client):
    pid = make(client).json()["id"]
    assert client.delete(f"/api/projects/{pid}").status_code == 204
    assert client.get(f"/api/projects/{pid}").status_code == 404


def test_list_is_ordered_by_chapter(client):
    for ch in (3, 1, 2):
        make(client, chapter=ch)
    chapters = [p["chapter"] for p in client.get("/api/projects").json()]
    assert chapters == [1, 2, 3]
