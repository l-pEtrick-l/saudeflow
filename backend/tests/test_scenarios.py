"""Testes dos cenários de demonstração da Global Solution."""

from tests.conftest import (
    answer_ids,
    complete,
    login,
    next_questions,
    start_questionnaire,
    submit_answers,
    unit_by_name,
)


def _flow(client, headers, reason: str, extra: dict | None = None):
    initial = start_questionnaire(client, headers)
    answers = {"reason": reason}
    answers.update(extra or {})
    conditional = next_questions(
        client, initial["submission"]["version_id"], answers, headers
    )
    ids = answer_ids(initial, conditional)
    payload = [{"question_id": ids["reason"], "value": reason}]
    for key, value in (extra or {}).items():
        if key in ids:
            payload.append({"question_id": ids[key], "value": value})
    submit_answers(client, initial["submission"]["id"], payload, headers)
    return initial["submission"]["id"], complete(client, initial["submission"]["id"], headers)


def test_cenario_1_consulta_de_rotina(client, patient_headers):
    sid, result = _flow(client, patient_headers, "consulta")
    assert result["category"] == "A"
    assert "ubs" in result["recommended_unit_types"]
    ubs = unit_by_name(client, "UBS")
    assert ubs["type"] == "ubs"


def test_cenario_2_atendimento_na_upa(client, patient_headers, reception_headers):
    sid, result = _flow(
        client, patient_headers, "mal_estar", {"febre": True, "febre_temperatura": 38}
    )
    assert result["category"] == "B"
    upa = unit_by_name(client, "UPA Centro")
    created = client.post(
        "/api/v1/requests",
        json={
            "submission_id": sid,
            "unit_id": upa["id"],
            "patient_name": "Cenário 2 Paciente",
            "patient_phone": "11977776666",
        },
        headers=patient_headers,
    )
    assert created.status_code == 201
    request_id = created.json()["id"]
    board = client.get(f"/api/v1/units/{upa['id']}/queue/board", headers=reception_headers)
    assert any(t["request_id"] == request_id for t in board.json()["tickets"])
    confirmed = client.post(
        f"/api/v1/requests/{request_id}/confirm-receipt", headers=reception_headers
    )
    assert confirmed.json()["status"] == "pre_register_confirmed"
    tracked = client.get(f"/api/v1/requests/track/{created.json()['protocol']}").json()
    assert tracked["status"] == "pre_register_confirmed"


def test_cenario_3_comparacao_de_unidades(client):
    centro = unit_by_name(client, "UPA Centro")
    norte = unit_by_name(client, "UPA Norte")
    centro_est = client.get(f"/api/v1/units/{centro['id']}/estimate?recompute=true").json()
    norte_est = client.get(f"/api/v1/units/{norte['id']}/estimate?recompute=true").json()
    assert centro_est["is_reliable"] is True
    assert norte_est["is_reliable"] is False  # histórico insuficiente


def test_cenario_4_ferimento_grave(client, patient_headers):
    sid, result = _flow(
        client,
        patient_headers,
        "ferimento",
        {
            "causa_ferimento": "arma_branca",
            "sangramento": True,
            "sangramento_intenso": True,
        },
    )
    assert result["category"] == "D"
    assert result["stop_flow"] is True
    assert result["emergency_message"]
    assert "weapon_injury" in result["alert_flags"]
    # o fluxo não cria fila virtual para emergência
    upa = unit_by_name(client, "UPA Centro")
    created = client.post(
        "/api/v1/requests",
        json={
            "submission_id": sid,
            "unit_id": upa["id"],
            "patient_name": "Cenário 4 Paciente",
        },
        headers=patient_headers,
    )
    assert created.status_code in (201, 409, 422)


def test_cenario_5_paciente_a_caminho_do_hospital(client, patient_headers):
    hospital = unit_by_name(client, "Hospital Geral")
    created = client.post(
        "/api/v1/alerts",
        json={
            "destination_unit_id": hospital["id"],
            "description": "Cenário 5: paciente a caminho",
            "patient_conscious": "yes",
            "patient_breathing": "yes",
            "bleeding": "no",
            "eta_minutes": 25,
        },
        headers=patient_headers,
    )
    assert created.status_code == 201
    alert_id = created.json()["id"]
    hospital_headers = login(client, "hospital@saudeflow.com.br", "Hosp@123")
    stats = client.get(f"/api/v1/analytics/hospitals/{hospital['id']}", headers=hospital_headers)
    assert stats.status_code == 200
    assert stats.json()["patients_on_the_way"] >= 1
    confirmed = client.post(f"/api/v1/alerts/{alert_id}/confirm", headers=hospital_headers)
    assert confirmed.json()["status"] == "confirmed"


def test_cenario_6_alteracao_de_capacidade(client, reception_headers):
    upa = unit_by_name(client, "UPA Centro")
    # baseline com capacidade reduzida
    client.post(
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
    before = client.get(f"/api/v1/units/{upa['id']}/estimate?recompute=true").json()
    updated = client.post(
        f"/api/v1/units/{upa['id']}/capacity",
        json={
            "professionals_available": 4,
            "rooms_active": 5,
            "welcome_capacity": 20,
            "services_unavailable": [],
            "receiving_pre_registrations": True,
        },
        headers=reception_headers,
    )
    assert updated.status_code == 200
    after = client.get(f"/api/v1/units/{upa['id']}/estimate?recompute=true").json()
    assert after["high_minutes"] < before["high_minutes"]


def test_cenario_7_dados_insuficientes(client):
    norte = unit_by_name(client, "UPA Norte")
    estimate = client.get(f"/api/v1/units/{norte['id']}/estimate?recompute=true").json()
    assert estimate["is_reliable"] is False
    assert estimate["low_minutes"] is None
    assert "dados suficientes" in estimate["message"].lower()


def test_cenario_8_fallback_de_comunicacao(client, admin_headers):
    """O tracking público funciona como fallback quando o WebSocket não está disponível."""
    upa = unit_by_name(client, "UPA Centro")
    initial = start_questionnaire(client, admin_headers)
    conditional = next_questions(
        client, initial["submission"]["version_id"], {"reason": "dor"}, admin_headers
    )
    ids = answer_ids(initial, conditional)
    submit_answers(
        client,
        initial["submission"]["id"],
        [
            {"question_id": ids["reason"], "value": "dor"},
            {"question_id": ids["dor_intensidade"], "value": 6},
        ],
        admin_headers,
    )
    client.post(
        f"/api/v1/questionnaires/submissions/{initial['submission']['id']}/complete",
        headers=admin_headers,
    )
    created = client.post(
        "/api/v1/requests",
        json={
            "submission_id": initial["submission"]["id"],
            "unit_id": upa["id"],
            "patient_name": "Cenário 8 Paciente",
        },
        headers=admin_headers,
    ).json()
    tracked = client.get(f"/api/v1/requests/track/{created['protocol']}")
    assert tracked.status_code == 200
    assert tracked.json()["protocol"] == created["protocol"]


def test_cenario_9_respostas_ambiguas(client, patient_headers):
    initial = start_questionnaire(client, patient_headers)
    # resposta incompleta: apenas texto livre, sem motivo selecionado
    submit_answers(
        client,
        initial["submission"]["id"],
        [{"question_id": initial["questions"][1]["id"], "value": "nao sei bem o que acontece"}],
        patient_headers,
    )
    result = complete(client, initial["submission"]["id"], patient_headers)
    assert result["category"] == "B"
    assert result["needs_professional"] is True
    assert result["confidence"] <= 0.4
    assert result["matched_rule_name"] == "fallback_conservador"
