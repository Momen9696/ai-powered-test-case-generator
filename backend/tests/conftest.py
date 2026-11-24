import os

os.environ["APP_DISABLE_DOTENV"] = "1"
os.environ["OPENAI_API_KEY"] = ""
os.environ["ANTHROPIC_API_KEY"] = ""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setenv("APP_DISABLE_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("AI_PROVIDER", "mock")
    from app.main import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def create_project(client: TestClient, name: str = "Payments") -> str:
    response = client.post("/api/projects", json={"name": name, "description": "QA project"})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def create_source(client: TestClient, project_id: str, content: str, kind: str = "user_story") -> str:
    response = client.post(
        f"/api/projects/{project_id}/sources",
        json={"kind": kind, "title": "Story", "content": content},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]
