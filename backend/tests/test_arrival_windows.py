from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.database import SessionLocal
from app.models.request import CareRequest
from app.repositories import queue_repo
from tests.conftest import unit_by_name
from tests.test_scenarios import _flow


def create_scheduled(client, patient_headers):
    sid, _ = _flow(client, patient_headers, "mal_estar", {"febre": True, "febre_temperatura": 38})
    upa = unit_by_name(client, "UPA Centro")
    options = client.get(f"/api/v1/units/{upa['id']}/arrival-windows").json()
    assert len(options["windows"]) == 6
    payload = {"submission_id": sid, "unit_id": upa["id"], "patient_name": f"Fila {uuid4()}",
               "arrival_window_start": options["windows"][1]["start"]}
    response = client.post("/api/v1/requests", json=payload, headers=patient_headers)
    assert response.status_code == 201, response.text
    return response.json(), payload


def test_schedule_tracking_checkin_and_finish(client, patient_headers, reception_headers):
    request, payload = create_scheduled(client, patient_headers)
    rid = request["id"]
    assert datetime.fromisoformat(request["arrival_window_start"]) == datetime.fromisoformat(payload["arrival_window_start"])
    queue = client.get(f"/api/v1/requests/track/{request['protocol']}").json()["queue"]
    assert queue["position"] >= 1
    assert queue["people_ahead"] == queue["position"] - 1
    assert queue["expected_arrival_start"]
    assert "patient_name" not in queue
    assert client.post(f"/api/v1/requests/{rid}/confirm-receipt", headers=reception_headers).json()["ticket"]["status"] == "waiting"
    with SessionLocal() as db:
        next_ticket = queue_repo.next_waiting(db, request["unit_id"])
        assert not next_ticket or next_ticket.request_id != rid
    assert client.post(f"/api/v1/requests/{rid}/checkin", json={}, headers=reception_headers).status_code == 200
    assert client.post(f"/api/v1/requests/{rid}/checkin", json={}, headers=reception_headers).status_code == 409
    queue = client.get(f"/api/v1/requests/track/{request['protocol']}").json()["queue"]
    assert queue["expected_arrival_start"] is None
    assert "Chegada registrada" in queue["message"]
    assert client.post(f"/api/v1/requests/{rid}/care-start", json={}, headers=reception_headers).status_code == 200
    assert client.post(f"/api/v1/requests/{rid}/care-finish", json={}, headers=reception_headers).status_code == 200
    queue = client.get(f"/api/v1/requests/track/{request['protocol']}").json()["queue"]
    assert queue["position"] is None


def test_invalid_windows_and_duplicate(client, patient_headers):
    request, payload = create_scheduled(client, patient_headers)
    assert client.post("/api/v1/requests", json=payload, headers=patient_headers).status_code == 409
    for start in [(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat(),
                  (datetime.now(timezone.utc)+timedelta(days=20)).isoformat(), "2026-12-01T12:00:00"]:
        invalid = dict(payload, patient_name=f"Inválido {uuid4()}", arrival_window_start=start)
        assert client.post("/api/v1/requests", json=invalid, headers=patient_headers).status_code == 422


def test_cancel_removes_position(client, patient_headers):
    request, _ = create_scheduled(client, patient_headers)
    assert client.post(f"/api/v1/requests/{request['id']}/cancel", json={"reason": "Não vou mais"}, headers=patient_headers).status_code == 200
    queue = client.get(f"/api/v1/requests/track/{request['protocol']}").json()["queue"]
    assert queue["position"] is None
    assert queue["expected_arrival_start"] is None


def test_position_moves_after_cancellation(client, patient_headers):
    first, _ = create_scheduled(client, patient_headers)
    second, _ = create_scheduled(client, patient_headers)
    track_url = f"/api/v1/requests/track/{second['protocol']}"
    before = client.get(track_url).json()["queue"]["position"]
    client.post(f"/api/v1/requests/{first['id']}/cancel", json={"reason": "Cancelar teste"}, headers=patient_headers)
    assert client.get(track_url).json()["queue"]["position"] == before - 1


def test_prediction_unavailable_when_capacity_is_zero(client, patient_headers, reception_headers):
    request, _ = create_scheduled(client, patient_headers)
    endpoint = f"/api/v1/units/{request['unit_id']}/capacity"
    capacity = {"professionals_available": 0, "rooms_active": 2, "welcome_capacity": 10,
                "services_unavailable": [], "receiving_pre_registrations": True}
    try:
        assert client.post(endpoint, json=capacity, headers=reception_headers).status_code == 200
        queue = client.get(f"/api/v1/requests/track/{request['protocol']}").json()["queue"]
        assert queue["expected_arrival_start"] is None
        assert "indisponível" in queue["message"]
        assert client.get(f"/api/v1/units/{request['unit_id']}/arrival-windows").json()["windows"] == []
    finally:
        client.post(endpoint, json=dict(capacity, professionals_available=3), headers=reception_headers)


def test_no_windows_without_data_or_for_ubs(client):
    for name in ["UPA Norte", "UBS"]:
        unit = unit_by_name(client, name)
        assert client.get(f"/api/v1/units/{unit['id']}/arrival-windows").json()["windows"] == []


def test_patient_cannot_mark_own_arrival(client, patient_headers):
    request, _ = create_scheduled(client, patient_headers)
    rid = request["id"]
    assert client.patch(f"/api/v1/requests/{rid}/status", json={"status": "patient_arrived"}, headers=patient_headers).status_code == 403
    assert client.post(f"/api/v1/requests/{rid}/checkin", json={}, headers=patient_headers).status_code == 403


def test_other_patient_cannot_schedule_from_submission(client, patient_headers):
    _, payload = create_scheduled(client, patient_headers)
    other = client.post("/api/v1/auth/register", json={"email": f"{uuid4()}@example.com", "password": "Teste@12345", "full_name": "Outro paciente"}).json()
    headers = {"Authorization": f"Bearer {other['access_token']}"}
    assert client.post("/api/v1/requests", json=dict(payload, patient_name="Outro paciente"), headers=headers).status_code == 403


def test_emergency_cannot_join_queue(client, patient_headers):
    sid, _ = _flow(client, patient_headers, "ferimento", {"causa_ferimento": "arma_branca", "sangramento": True, "sangramento_intenso": True})
    upa = unit_by_name(client, "UPA Centro")
    assert client.post("/api/v1/requests", json={"submission_id": sid, "unit_id": upa["id"], "patient_name": "Emergência teste"}, headers=patient_headers).status_code == 422
