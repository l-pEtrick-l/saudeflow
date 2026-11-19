"""Motor de regras de orientação — componente puro, determinístico e testável.

NÃO implementa diagnóstico médico. As regras são exemplos acadêmicos conservadores
que precisam de validação clínica antes de qualquer uso real.
"""

from __future__ import annotations

import statistics
from typing import Any, Dict, List, Optional

CATEGORY_LABELS = {
    "A": "Atenção básica / UBS",
    "B": "Possível atendimento em UPA",
    "C": "Possível necessidade de hospital ou pronto-socorro",
    "D": "Possível emergência grave — SAMU 192",
}

CATEGORY_SERVICE = {
    "A": "atencao_basica",
    "B": "upa",
    "C": "hospital",
    "D": "emergencia",
}

CATEGORY_UNIT_TYPES = {
    "A": ["ubs"],
    "B": ["upa", "emergency"],
    "C": ["hospital", "emergency"],
    "D": ["emergency"],
}

EMERGENCY_MESSAGE = (
    "Com base no relato, pode ser necessária ajuda imediata. Ligue agora para o SAMU 192 "
    "(ou vá a um pronto-socorro se já estiver sendo acompanhado). Este sistema não substitui "
    "o atendimento de emergência nem a regulação médica."
)

# Palavras explícitas de emergência no texto livre. Reforçam (nunca reduzem) a orientação.
TEXT_EMERGENCY_KEYWORDS = {
    "arma branca": "weapon_injury",
    "arma de fogo": "weapon_injury",
    "tiroteio": "weapon_injury",
    "desmai": "loss_of_consciousness",
    "desmaio": "loss_of_consciousness",
    "inconscient": "loss_of_consciousness",
    "convuls": "seizure",
    "avc": "stroke",
    "derrame": "stroke",
    "infart": "chest_emergency",
    "ataque cardíaco": "chest_emergency",
    "enfart": "chest_emergency",
    "sem respirar": "respiratory_emergency",
    "não respira": "respiratory_emergency",
    "nao respira": "respiratory_emergency",
    "afog": "respiratory_emergency",
    "sangramento intenso": "severe_bleeding",
    "muito sangue": "severe_bleeding",
    "atropel": "severe_trauma",
    "queda de moto": "severe_trauma",
    "acidente grave": "severe_trauma",
}

EMERGENCY_FLAGS = set(TEXT_EMERGENCY_KEYWORDS.values()) | {
    "loss_of_consciousness",
    "seizure",
    "stroke",
    "chest_emergency",
    "respiratory_emergency",
    "severe_bleeding",
    "weapon_injury",
    "severe_trauma",
}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def condition_matches(cond: Optional[Dict[str, Any]], answers: Dict[str, Any]) -> bool:
    """Avalia uma condição contra o mapa de respostas (external_id -> valor)."""
    if not cond:
        return True
    if "all" in cond:
        return all(condition_matches(c, answers) for c in cond["all"])
    if "any" in cond:
        return any(condition_matches(c, answers) for c in cond["any"])
    if "not" in cond:
        return not condition_matches(cond["not"], answers)

    question = cond.get("question")
    if not question:
        return True
    value = answers.get(question)

    if "exists" in cond:
        present = value is not None and value != "" and value != []
        return present == bool(cond["exists"])
    if value is None:
        return False
    if "eq" in cond:
        return value == cond["eq"]
    if "ne" in cond:
        return value != cond["ne"]
    if "in" in cond:
        options = cond["in"] or []
        if isinstance(value, list):
            return any(v in options for v in value)
        return value in options
    if "not_in" in cond:
        options = cond["not_in"] or []
        if isinstance(value, list):
            return not any(v in options for v in value)
        return value not in options
    if "contains" in cond:
        return str(cond["contains"]).lower() in str(value).lower()
    if _is_number(value):
        if "gt" in cond:
            return value > cond["gt"]
        if "gte" in cond:
            return value >= cond["gte"]
        if "lt" in cond:
            return value < cond["lt"]
        if "lte" in cond:
            return value <= cond["lte"]
    return False


def collect_alert_flags(questions: List[Dict[str, Any]], answers: Dict[str, Any]) -> List[str]:
    """Sinais de alerta declarados em opções e perguntas, quando a condição é atendida."""
    flags: List[str] = []
    for question in questions or []:
        external_id = question.get("external_id")
        value = answers.get(external_id)
        values = value if isinstance(value, list) else [value]
        for option in question.get("options") or []:
            if option.get("alert_flag") and option.get("code") in values:
                flags.append(option["alert_flag"])
        for item in question.get("alert_flags") or []:
            if not isinstance(item, dict):
                continue
            when = item.get("when") or {}
            flag = item.get("flag")
            if not flag:
                continue
            if not when:
                flags.append(flag)
            else:
                # a condição do alerta é relativa à própria pergunta
                cond = {"question": external_id, **when}
                if condition_matches(cond, answers):
                    flags.append(flag)
    return sorted(set(flags))


def collect_text_flags(free_text: str) -> List[str]:
    from app.utils import normalize_text

    text = normalize_text(free_text or "")
    return sorted(
        {flag for keyword, flag in TEXT_EMERGENCY_KEYWORDS.items() if keyword in text}
    )


def _render_template(template: Optional[str], answers: Dict[str, Any]) -> str:
    if not template:
        return ""
    result = template
    for key, value in answers.items():
        if isinstance(value, (str, int, float, bool)):
            result = result.replace("{" + key + "}", str(value))
    return result


def evaluate_guidance(
    rules: List[Dict[str, Any]],
    answers: Dict[str, Any],
    questions: Optional[List[Dict[str, Any]]] = None,
    free_text: str = "",
    rule_set_version: str = "",
) -> Dict[str, Any]:
    """Avalia regras em ordem de prioridade e retorna orientação estruturada.

    Determinístico: mesma versão de regras + mesmas respostas => mesmo resultado.
    """
    question_flags = collect_alert_flags(questions or [], answers)
    text_flags = collect_text_flags(free_text)
    all_flags = sorted(set(question_flags) | set(text_flags))

    ordered = sorted(
        [r for r in (rules or []) if r.get("is_active", True)],
        key=lambda r: (int(r.get("priority", 100)), str(r.get("name", ""))),
    )

    for rule in ordered:
        if not condition_matches(rule.get("conditions"), answers):
            continue
        flags = sorted(set(all_flags) | set(rule.get("alert_flags") or []))
        category = rule.get("category", "B")
        return {
            "category": category,
            "category_label": CATEGORY_LABELS.get(category, category),
            "service_type": rule.get("service_hint") or CATEGORY_SERVICE.get(category, "upa"),
            "alert_flags": flags,
            "justification": _render_template(
                rule.get("message_template"), answers
            ).strip(),
            "confidence": float(rule.get("confidence", 0.5)),
            "stop_flow": bool(rule.get("stop_flow", False)),
            "needs_professional": bool(rule.get("needs_professional", True)),
            "recommended_unit_types": rule.get("recommended_unit_types")
            or CATEGORY_UNIT_TYPES.get(category, ["upa"]),
            "rule_set_version": rule_set_version or rule.get("rule_set_version", ""),
            "matched_rule_id": rule.get("id"),
            "matched_rule_name": rule.get("name"),
            "emergency_message": EMERGENCY_MESSAGE if category == "D" else None,
        }

    # Nenhuma regra casou: se houver sinal de emergência, resposta conservadora máxima.
    if set(text_flags) & EMERGENCY_FLAGS or set(question_flags) & EMERGENCY_FLAGS:
        return {
            "category": "D",
            "category_label": CATEGORY_LABELS["D"],
            "service_type": "emergencia",
            "alert_flags": all_flags,
            "justification": (
                "Foram identificados sinais de possível emergência no relato, mas nenhuma "
                "regra específica casou. Por segurança, a orientação é procurar socorro "
                "imediato (SAMU 192)."
            ),
            "confidence": 0.4,
            "stop_flow": True,
            "needs_professional": True,
            "recommended_unit_types": ["emergency"],
            "rule_set_version": rule_set_version,
            "matched_rule_id": None,
            "matched_rule_name": "fallback_emergencia_texto",
            "emergency_message": EMERGENCY_MESSAGE,
        }

    # Fallback conservador: não concluir baixa gravidade por ausência de sinais.
    return {
        "category": "B",
        "category_label": CATEGORY_LABELS["B"],
        "service_type": "upa",
        "alert_flags": all_flags,
        "justification": (
            "As respostas foram insuficientes, ambíguas ou não casaram com nenhuma regra "
            "específica. A orientação conservadora é buscar avaliação em uma UPA. "
            "Isso não descarta a necessidade de atendimento presencial."
        ),
        "confidence": 0.3,
        "stop_flow": False,
        "needs_professional": True,
        "recommended_unit_types": ["upa", "emergency"],
        "rule_set_version": rule_set_version,
        "matched_rule_id": None,
        "matched_rule_name": "fallback_conservador",
        "emergency_message": None,
    }


def visible_questions(
    questions: List[Dict[str, Any]], answers: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Retorna as perguntas visíveis dado o mapa atual de respostas."""
    visible = []
    for question in sorted(questions or [], key=lambda q: int(q.get("order_index", 0))):
        logic = question.get("conditional_logic") or {}
        show_if = logic.get("show_if")
        if show_if and not condition_matches(show_if, answers):
            continue
        visible.append(question)
    return visible


def compute_wait_estimate(
    durations: List[float],
    waiting_count: int,
    professionals_available: int,
    min_sample: int = 5,
) -> Dict[str, Any]:
    """Calcula faixa de espera explicável (mediana dos tempos x taxa de processamento).

    Retorna is_reliable=False quando os dados são insuficientes — nunca inventa tempo.
    """
    clean = sorted(float(d) for d in (durations or []) if d is not None and d > 0)
    sample_size = len(clean)
    result = {
        "is_reliable": False,
        "low_minutes": None,
        "p50_minutes": None,
        "high_minutes": None,
        "sample_size": sample_size,
        "method": "median_duration_x_throughput_v1",
        "message": "",
    }
    if sample_size < min_sample:
        result["message"] = (
            "Não há dados suficientes para estimar a espera desta unidade. "
            "A unidade não informou tempos de atendimento recentes em quantidade mínima."
        )
        return result
    if professionals_available <= 0:
        result["message"] = (
            "A unidade informou não haver profissionais disponíveis no momento; "
            "não é possível estimar a espera."
        )
        return result

    p50 = statistics.median(clean)
    mean = statistics.fmean(clean)
    # throughput: pacientes por hora = profissionais * (60 / tempo médio)
    throughput = professionals_available * (60.0 / mean) if mean > 0 else 0.0
    if throughput <= 0:
        result["message"] = "Não foi possível calcular a taxa de processamento."
        return result

    base_wait = (max(waiting_count, 0) / throughput) * 60.0
    if waiting_count <= 0:
        result.update(
            {
                "is_reliable": True,
                "low_minutes": 0,
                "p50_minutes": round(p50 / 5.0) * 5,
                "high_minutes": 0,
                "message": (
                    "Nenhuma pessoa aguardando no momento. "
                    "A estimativa será calculada quando houver fila."
                ),
            }
        )
        return result
    low = max(0.0, base_wait * 0.75)
    high = base_wait * 1.35
    low_r = round(low / 5.0) * 5
    high_r = round(high / 5.0) * 5
    p50_r = round(p50 / 5.0) * 5
    result.update(
        {
            "is_reliable": True,
            "low_minutes": low_r,
            "p50_minutes": p50_r,
            "high_minutes": high_r,
            "message": (
                f"Espera estimada: {int(low_r)}–{int(high_r)} minutos "
                f"(mediana dos atendimentos recentes: {int(p50_r)} min; "
                f"{professionals_available} profissional(is) informado(s)). "
                "Estimativa operacional, não garantia de atendimento."
            ),
        }
    )
    return result
