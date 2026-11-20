"""Administrative arrival planning for the academic UPA demonstration."""
import math
from datetime import datetime, timedelta, timezone

from app.exceptions import UnprocessableError
from app.repositories import queue_repo, unit_repo
from app.services import estimate_service, unit_service


def utc(value):
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def windows(db, unit_id):
    unit = unit_repo.get_unit(db, unit_id)
    capacity = unit_service.current_capacity(db, unit_id)
    if not unit or not unit.is_active or unit.type != "upa" or not capacity.get("receiving_pre_registrations"):
        return {"windows": [], "message": "Esta unidade não oferece planejamento de chegada agora."}
    estimate = estimate_service.get_estimate(db, unit_id, recompute=True)
    if not estimate.is_reliable:
        return {"windows": [], "message": "Sem histórico suficiente para sugerir uma faixa de chegada. Você pode fazer o pré-cadastro sem horário."}
    now = datetime.now(timezone.utc)
    first = now + timedelta(minutes=max(30, estimate.low_minutes or 0))
    first = datetime.fromtimestamp(math.ceil(first.timestamp() / 1800) * 1800, timezone.utc)
    return {"windows": [{"start": first + timedelta(minutes=30*i), "end": first + timedelta(minutes=30*(i+1))} for i in range(6)],
            "message": "Escolha uma faixa aproximada de chegada. Acompanhe as mudanças pelo protocolo; não é uma consulta com hora marcada."}


def validate_window(db, unit_id, start, category):
    if start is None:
        return None
    if category != "B" or start.tzinfo is None:
        raise UnprocessableError("A fila online com horário está disponível apenas para orientação de UPA; informe uma data com fuso horário.")
    options = windows(db, unit_id)["windows"]
    start = utc(start)
    if not any(w["start"] == start for w in options):
        raise UnprocessableError("Esta faixa não está mais disponível. Atualize os horários e escolha novamente.")
    return start


def tracking(db, request):
    ticket = queue_repo.get_ticket_for_request(db, request.id)
    active = request.status not in ("finished", "cancelled") and ticket and ticket.status not in ("done", "cancelled", "absent")
    waiting = [t for t in queue_repo.list_tickets(db, request.unit_id) if t.status == "waiting"]
    position = next((i + 1 for i, t in enumerate(waiting) if t.id == ticket.id), None) if active else None
    result = {"ticket_number": request.protocol, "position": position,
              "people_ahead": position - 1 if position else None,
              "arrival_window_start": utc(request.arrival_window_start),
              "arrival_window_end": utc(request.arrival_window_end),
              "expected_arrival_start": None, "expected_arrival_end": None,
              "updated_at": datetime.now(timezone.utc), "message": "A posição é administrativa; a prioridade clínica é definida presencialmente."}
    if not request.arrival_window_start or not active:
        return result
    if request.status in ("patient_arrived", "awaiting_welcome", "awaiting_care", "in_care"):
        result["message"] = "Chegada registrada. Aguarde a orientação da equipe na unidade."
        return result
    capacity = unit_service.current_capacity(db, request.unit_id)
    durations = queue_repo.recent_durations(db, request.unit_id)
    from app.services.guidance_engine import compute_wait_estimate
    estimate = compute_wait_estimate(durations, max(0, (position or 1)-1), capacity.get("professionals_available", 0))
    if not estimate["is_reliable"] or not capacity.get("receiving_pre_registrations"):
        result["message"] = "Previsão temporariamente indisponível. Consulte a unidade; a faixa escolhida não garante atendimento."
        return result
    now = datetime.now(timezone.utc)
    start = max(utc(request.arrival_window_start), now + timedelta(minutes=estimate["low_minutes"] or 0))
    end = max(start + timedelta(minutes=30), now + timedelta(minutes=estimate["high_minutes"] or 0))
    result.update(expected_arrival_start=start, expected_arrival_end=end,
                  message="Faixa estimada atualizada conforme a fila e a capacidade. Confira novamente antes de sair e apresente seu protocolo na recepção.")
    return result
