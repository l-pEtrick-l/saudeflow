import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_saudeflow.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("SYNC_ENABLED", "false")

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.seed import seed


@pytest.fixture(scope="session", autouse=True)
def _database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def login(client, email: str, password: str) -> dict:
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture()
def admin_headers(client):
    return login(client, "admin@saudeflow.com.br", "Admin@123")


@pytest.fixture()
def reception_headers(client):
    return login(client, "recepcao.upa@saudeflow.com.br", "Upa@123")


@pytest.fixture()
def patient_headers(client):
    return login(client, "paciente@saudeflow.com.br", "Paciente@123")


def unit_by_name(client, name_part: str):
    data = client.get("/api/v1/units").json()["data"]
    return next(u for u in data if name_part in u["name"])


def start_questionnaire(client, headers) -> dict:
    return client.get("/api/v1/questionnaires/active", headers=headers).json()


def next_questions(client, version_id, answers, headers) -> list:
    return client.post(
        f"/api/v1/questionnaires/versions/{version_id}/next",
        json={"answers": answers},
        headers=headers,
    ).json()


def answer_ids(initial, conditional) -> dict:
    return {q["external_id"]: q["id"] for q in initial["questions"] + conditional}


def submit_answers(client, submission_id, payload, headers):
    return client.post(
        f"/api/v1/questionnaires/submissions/{submission_id}/answers",
        json={"answers": payload},
        headers=headers,
    )


def complete(client, submission_id, headers) -> dict:
    response = client.post(
        f"/api/v1/questionnaires/submissions/{submission_id}/complete", headers=headers
    )
    assert response.status_code == 200, response.text
    return response.json()
