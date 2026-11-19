"""Testes do motor de orientação (componente puro, determinístico)."""

from app.services.guidance_engine import (
    CATEGORY_LABELS,
    condition_matches,
    evaluate_guidance,
    visible_questions,
)

RULES = [
    {
        "id": "r1",
        "name": "emergencia",
        "priority": 10,
        "category": "D",
        "service_hint": "emergencia",
        "conditions": {"any": [{"question": "causa", "in": ["arma_branca", "arma_fogo"]}]},
        "alert_flags": ["possible_emergency"],
        "confidence": 0.9,
        "stop_flow": True,
        "needs_professional": True,
        "message_template": "Procure socorro imediato.",
        "rule_set_version": "v1",
        "is_active": True,
    },
    {
        "id": "r2",
        "name": "upa",
        "priority": 30,
        "category": "B",
        "service_hint": "upa",
        "conditions": {"any": [{"question": "motivo", "in": ["mal_estar", "dor"]}]},
        "alert_flags": [],
        "confidence": 0.6,
        "stop_flow": False,
        "needs_professional": True,
        "message_template": "UPA pode ser adequada.",
        "rule_set_version": "v1",
        "is_active": True,
    },
    {
        "id": "r3",
        "name": "ubs",
        "priority": 40,
        "category": "A",
        "service_hint": "atencao_basica",
        "conditions": {"any": [{"question": "motivo", "eq": "consulta"}]},
        "alert_flags": [],
        "confidence": 0.7,
        "stop_flow": False,
        "needs_professional": False,
        "message_template": "Procure a UBS.",
        "rule_set_version": "v1",
        "is_active": True,
    },
]


def test_condition_operators():
    answers = {"a": True, "b": "x", "c": 9, "d": None, "e": ["x", "y"]}
    assert condition_matches({"eq": True}, answers) is True  # sem pergunta de referência
    assert condition_matches({"question": "a", "eq": True}, answers)
    assert condition_matches({"question": "b", "in": ["x", "z"]}, answers)
    assert condition_matches({"question": "c", "gte": 9}, answers)
    assert condition_matches({"question": "c", "lt": 10}, answers)
    assert condition_matches({"question": "e", "in": ["y"]}, answers)
    assert condition_matches({"question": "d", "exists": False}, answers)
    assert condition_matches({"not": {"question": "a", "eq": True}}, answers) is False
    assert condition_matches({"all": [{"question": "a", "eq": True}, {"question": "c", "gt": 5}]}, answers)
    assert condition_matches({"any": [{"question": "a", "eq": False}, {"question": "b", "eq": "x"}]}, answers)


def test_emergency_rule_interrupts_flow():
    result = evaluate_guidance(RULES, {"motivo": "ferimento", "causa": "arma_branca"})
    assert result["category"] == "D"
    assert result["stop_flow"] is True
    assert result["matched_rule_id"] == "r1"
    assert "possible_emergency" in result["alert_flags"]


def test_upa_and_ubs_categories():
    assert evaluate_guidance(RULES, {"motivo": "dor"})["category"] == "B"
    assert evaluate_guidance(RULES, {"motivo": "consulta"})["category"] == "A"
    assert evaluate_guidance(RULES, {"motivo": "consulta"})["recommended_unit_types"] == ["ubs"]


def test_fallback_is_conservative():
    result = evaluate_guidance(RULES, {})
    assert result["category"] == "B"
    assert result["confidence"] <= 0.4
    assert result["needs_professional"] is True
    assert result["matched_rule_name"] == "fallback_conservador"


def test_text_emergency_forces_category_d():
    result = evaluate_guidance(RULES, {"motivo": "outro"}, free_text="sangramento intenso")
    assert result["category"] == "D"
    assert result["stop_flow"] is True


def test_determinism():
    answers = {"motivo": "mal_estar", "causa": "arma_fogo"}
    first = evaluate_guidance(RULES, answers)
    second = evaluate_guidance(RULES, answers)
    assert first == second


def test_visible_questions_respect_conditions():
    questions = [
        {"external_id": "a", "order_index": 1, "conditional_logic": None},
        {"external_id": "b", "order_index": 2, "conditional_logic": {"show_if": {"question": "a", "eq": "x"}}},
        {"external_id": "c", "order_index": 3, "conditional_logic": {"show_if": {"question": "a", "eq": "y"}}},
    ]
    assert [q["external_id"] for q in visible_questions(questions, {"a": "x"})] == ["a", "b"]
    assert [q["external_id"] for q in visible_questions(questions, {"a": "y"})] == ["a", "c"]


def test_category_labels_exist():
    for category in ("A", "B", "C", "D"):
        assert category in CATEGORY_LABELS
