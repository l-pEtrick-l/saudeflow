"""Testes de API: autenticação, RBAC, unidades, solicitações, filas e alertas."""

import pytest

from tests.conftest import login, unit_by_name


def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_login_invalid(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@saudeflow.com.br", "password": "errada"},
    )
    assert response.status_code == 401


def test_patient_cannot_manage_users(client, patient_headers):
    response = client.get("/api/v1/users", headers=patient_headers)
    assert response.status_code == 403


def test_units_are_public_and_enriched(client):
    response = client.get("/api/v1/units")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) >= 5
    upa = next(u for u in data if u["type"] == "upa" and "Centro" in u["name"])
    assert upa["estimate"]["is_reliable"] is True
    assert upa["services"]
    assert "is_simulated" in upa and upa["is_simulated"] is True


def test_estimate_insufficient_data(client):
    upa_norte = unit_by_name(client, "UPA Norte")
    response = client.get(f"/api/v1/units/{upa_norte['id']}/estimate?recompute=true")
    assert response.status_code == 200
    body = response.json()
    assert body["is_reliable"] is False
    assert "dados suficientes" in body["message"].lower()


def test_create_request_and_track_public(client, admin_headers):
    upa = unit_by_name(client, "UPA Centro")
    initial = client.get("/api/v1/questionnaires/active", headers=admin_headers).json()
    conditional = client.post(
        f"/api/v1/questionnaires/versions/{initial['submission']['version_id']}/next",
        json={"answers": {"reason": "mal_estar"}},
        headers=admin_headers,
    ).json()
    ids = {q["external_id"]: q["id"] for q in initial["questions"] + conditional}
    extra = client.post(
        f"/api/v1/questionnaires/versions/{initial['submission']['version_id']}/next",
        json={"answers": {"reason": "mal_estar", "febre": True}},
        headers=admin_headers,
    ).json()
    ids.update({q["external_id"]: q["id"] for q in extra})
    client.post(
        f"/api/v1/questionnaires/submissions/{initial['submission']['id']}/answers",
        json={
            "answers": [
                {"question_id": ids["reason"], "value": "mal_estar"},
                {"question_id": ids["febre"], "value": True},
                {"question_id": ids["febre_temperatura"], "value": 38},
            ]
        },
        headers=admin_headers,
    )
    result = client.post(
        f"/api/v1/questionnaires/submissions/{initial['submission']['id']}/complete",
        headers=admin_headers,
    ).json()
    assert result["category"] == "B"

    created = client.post(
        "/api/v1/requests",
        json={
            "submission_id": initial["submission"]["id"],
            "unit_id": upa["id"],
            "patient_name": "Paciente API Teste",
            "patient_phone": "11988887777",
        },
        headers=admin_headers,
    )
    assert created.status_code == 201
    body = created.json()
    assert body["protocol"].startswith("SF-")
    assert body["status"] == "sent"

    tracked = client.get(f"/api/v1/requests/track/{body['protocol']}")
    assert tracked.status_code == 200
    assert tracked.json()["protocol"] == body["protocol"]
    # o tracking público não expõe relatos de saúde
    assert "complaint_summary" not in tracked.json()


def test_duplicate_request_rejected(client, admin_headers):
    upa = unit_by_name(client, "UPA Centro")
    initial = client.get("/api/v1/questionnaires/active", headers=admin_headers).json()
    client.post(
        f"/api/v1/questionnaires/submissions/{initial['submission']['id']}/answers",
        json={"answers": [{"question_id": initial["questions"][0]["id"], "value": "consulta"}]},
        headers=admin_headers,
    )
    payload = {
        "submission_id": initial["submission"]["id"],
        "unit_id": upa["id"],
        "patient_name": "Duplicado Teste",
    }
    first = client.post("/api/v1/requests", json=payload, headers=admin_headers)
    second = client.post("/api/v1/requests", json=payload, headers=admin_headers)
    assert first.status_code in (201, 409)
    assert second.status_code == 409


def test_rbac_queue_board(client, reception_headers, patient_headers):
    upa = unit_by_name(client, "UPA Centro")
    allowed = client.get(f"/api/v1/units/{upa['id']}/queue/board", headers=reception_headers)
    assert allowed.status_code == 200
    denied = client.get(f"/api/v1/units/{upa['id']}/queue/board", headers=patient_headers)
    assert denied.status_code == 403


def test_alert_lifecycle(client, patient_headers):
    from tests.conftest import login

    hospital = unit_by_name(client, "Hospital Geral")
    created = client.post(
        "/api/v1/alerts",
        json={
            "destination_unit_id": hospital["id"],
            "description": "Teste de pré-alerta",
            "patient_conscious": "yes",
            "patient_breathing": "yes",
            "bleeding": "no",
            "eta_minutes": 15,
        },
        headers=patient_headers,
    )
    assert created.status_code == 201
    alert_id = created.json()["id"]
    assert created.json()["status"] == "new"

    hospital_headers = login(client, "hospital@saudeflow.com.br", "Hosp@123")
    listed = client.get("/api/v1/alerts", headers=hospital_headers).json()["data"]
    assert any(a["id"] == alert_id for a in listed)

    confirmed = client.post(f"/api/v1/alerts/{alert_id}/confirm", headers=hospital_headers)
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "confirmed"

    patient_view = client.get(f"/api/v1/alerts/{alert_id}", headers=patient_headers)
    assert patient_view.status_code == 200
    assert patient_view.json()["status"] == "confirmed"


def test_notifications_for_patient(client, patient_headers):
    response = client.get("/api/v1/notifications", headers=patient_headers)
    assert response.status_code == 200
    assert "data" in response.json()


def test_analytics_admin_only(client, admin_headers, reception_headers):
    overview = client.get("/api/v1/analytics/overview", headers=admin_headers)
    assert overview.status_code == 200
    assert overview.json()["total_units"] >= 5
    denied = client.get("/api/v1/analytics/overview", headers=reception_headers)
    assert denied.status_code == 403


def test_capacity_change_recalculates_estimate(client, reception_headers):
    upa = unit_by_name(client, "UPA Centro")
    before = client.get(f"/api/v1/units/{upa['id']}/estimate?recompute=true").json()
    response = client.post(
        f"/api/v1/units/{upa['id']}/capacity",
        json={
            "professionals_available": 1,
            "rooms_active": 2,
            "welcome_capacity": 10,
            "services_unavailable": [],
            "receiving_pre_registrations": True,
        },
        headers=reception_headers,
    )
    assert response.status_code == 200
    after = client.get(f"/api/v1/units/{upa['id']}/estimate?recompute=true").json()
    assert after["is_reliable"] is True
    assert after["high_minutes"] > before["high_minutes"]


def test_viacep_cache(client):
    first = client.get("/api/v1/integrations/viacep/01001000")
    assert first.status_code == 200
    assert first.json()["localidade"] == "São Paulo"
    second = client.get("/api/v1/integrations/viacep/01001000")
    assert "cache" in second.json()["source"]


def test_audit_logs_admin(client, admin_headers):
    # gera uma ação auditável antes de consultar
    unit_by_name(client, "UPA Centro")
    client.post(
        "/api/v1/auth/login",
        json={"email": "admin@saudeflow.com.br", "password": "Admin@123"},
    )
    response = client.get("/api/v1/audit-logs", headers=admin_headers)
    assert response.status_code == 200
    assert "data" in response.json()
