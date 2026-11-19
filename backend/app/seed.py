"""Seed de demonstração — dados fictícios e idempotente.

Execute: python -m app.seed
Nenhum dado real de pacientes é utilizado.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.database import SessionLocal, init_db
from app.models.guidance import GuidanceRule
from app.models.questionnaire import (
    Question,
    QuestionOption,
    Questionnaire,
    QuestionnaireSubmission,
    QuestionnaireVersion,
)
from app.models.user import User
from app.repositories import (
    alert_repo,
    guidance_repo,
    queue_repo,
    request_repo,
    unit_repo,
    user_repo,
)
from app.security import hash_password
from app.utils import new_uuid

RULE_SET_VERSION = "2026.1-academico-v1"

DEMO_USERS = [
    ("admin@saudeflow.com.br", "Admin@123", "Administrador do Sistema", "admin", None),
    ("gestor.upa@saudeflow.com.br", "Upa@123", "Gestora da UPA Centro", "manager", "upa_centro"),
    ("recepcao.upa@saudeflow.com.br", "Upa@123", "Recepcionista da UPA Centro", "receptionist", "upa_centro"),
    ("classificador.upa@saudeflow.com.br", "Upa@123", "Enfermeiro de Classificação", "classifier", "upa_centro"),
    ("operador.norte@saudeflow.com.br", "Upa@123", "Operador da UPA Norte", "operator", "upa_norte"),
    ("hospital@saudeflow.com.br", "Hosp@123", "Equipe do Hospital Geral", "hospital_staff", "hospital"),
    ("paciente@saudeflow.com.br", "Paciente@123", "Paciente de Demonstração", "patient", None),
]


def seed(db: Session) -> Dict[str, Any]:
    stats = {"seeded": False, "units": 0, "users": 0, "rules": 0, "questions": 0}
    user_repo.ensure_roles_and_permissions(db)

    if user_repo.get_by_email(db, "admin@saudeflow.com.br"):
        return stats

    units = _seed_units(db)
    stats["units"] = len(units)

    for email, password, name, role, unit_key in DEMO_USERS:
        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=name,
            phone="(11) 99999-0000",
        )
        db.add(user)
        db.flush()
        unit_id = units.get(unit_key) if unit_key else None
        user_repo.assign_role(db, user.id, role, unit_id)
        stats["users"] += 1

    version = _seed_questionnaire(db)
    stats["questions"] = len(_QUESTIONS)
    stats["rules"] = _seed_rules(db)
    _seed_history(db, units)
    patient = db.query(User).filter_by(email="paciente@saudeflow.com.br").first()
    _seed_alert(db, units, patient)

    db.commit()
    stats["seeded"] = True
    stats["rule_set_version"] = RULE_SET_VERSION
    return stats


def _seed_units(db: Session) -> Dict[str, str]:
    specs = [
        (
            "ubs",
            {
                "name": "UBS Parque das Flores (Simulada)",
                "type": "ubs",
                "is_simulated": True,
                "street": "Rua das Flores",
                "number": "120",
                "neighborhood": "Parque das Flores",
                "city": "São Paulo",
                "state": "SP",
                "postal_code": "05650-000",
                "latitude": -23.5605,
                "longitude": -46.6533,
                "phone": "(11) 3555-0100",
            },
            [
                {"service_code": "consulta", "service_name": "Consulta de rotina"},
                {"service_code": "vacina", "service_name": "Vacinação"},
                {"service_code": "receita", "service_name": "Renovação de receitas"},
            ],
        ),
        (
            "upa_centro",
            {
                "name": "UPA Centro (Simulada)",
                "type": "upa",
                "is_simulated": True,
                "street": "Avenida Paulista",
                "number": "1000",
                "neighborhood": "Bela Vista",
                "city": "São Paulo",
                "state": "SP",
                "postal_code": "01310-100",
                "latitude": -23.5605,
                "longitude": -46.6560,
                "phone": "(11) 3555-0200",
            },
            [
                {"service_code": "clinico", "service_name": "Clínico geral"},
                {"service_code": "pediatria", "service_name": "Pediatria"},
                {"service_code": "ortopedia", "service_name": "Ortopedia"},
                {"service_code": "enfermagem", "service_name": "Enfermagem"},
            ],
        ),
        (
            "upa_norte",
            {
                "name": "UPA Norte (Simulada)",
                "type": "upa",
                "is_simulated": True,
                "street": "Rua da Santana",
                "number": "500",
                "neighborhood": "Santana",
                "city": "São Paulo",
                "state": "SP",
                "postal_code": "02020-000",
                "latitude": -23.4950,
                "longitude": -46.6250,
                "phone": "(11) 3555-0300",
            },
            [
                {"service_code": "clinico", "service_name": "Clínico geral"},
                {"service_code": "enfermagem", "service_name": "Enfermagem"},
            ],
        ),
        (
            "hospital",
            {
                "name": "Hospital Geral Simulado",
                "type": "hospital",
                "is_simulated": True,
                "street": "Rua do Hospital",
                "number": "200",
                "neighborhood": "Vila Mariana",
                "city": "São Paulo",
                "state": "SP",
                "postal_code": "04110-000",
                "latitude": -23.5950,
                "longitude": -46.6400,
                "phone": "(11) 3555-0400",
            },
            [
                {"service_code": "pronto_socorro", "service_name": "Pronto-socorro"},
                {"service_code": "internacao", "service_name": "Internação"},
                {"service_code": "centro_cirurgico", "service_name": "Centro cirúrgico"},
                {"service_code": "uti", "service_name": "UTI"},
            ],
        ),
        (
            "ps",
            {
                "name": "Pronto-Socorro Municipal Simulado",
                "type": "emergency",
                "is_simulated": True,
                "street": "Avenida Brasil",
                "number": "300",
                "neighborhood": "Jardins",
                "city": "São Paulo",
                "state": "SP",
                "postal_code": "01400-000",
                "latitude": -23.5700,
                "longitude": -46.6650,
                "phone": "(11) 3555-0500",
            },
            [
                {"service_code": "emergencia", "service_name": "Emergência adulto"},
                {"service_code": "emergencia_ped", "service_name": "Emergência pediátrica"},
            ],
        ),
    ]

    units: Dict[str, str] = {}
    for key, data, services in specs:
        unit = unit_repo.create_unit(db, data, services)
        units[key] = unit.id

    capacities = {
        "ubs": (2, 2, 10),
        "upa_centro": (6, 8, 30),
        "upa_norte": (2, 3, 10),
        "hospital": (10, 12, 40),
        "ps": (8, 10, 30),
    }
    for key, (prof, rooms, welcome) in capacities.items():
        unit_repo.add_capacity(
            db,
            units[key],
            {
                "professionals_available": prof,
                "rooms_active": rooms,
                "welcome_capacity": welcome,
                "services_unavailable": [],
                "receiving_pre_registrations": True,
                "notes": "Capacidade de demonstração",
            },
            None,
        )
    return units


_QUESTIONS: List[Dict[str, Any]] = [
    {
        "external_id": "reason",
        "text": "O que você precisa?",
        "type": "single_choice",
        "required": True,
        "order": 1,
        "help_text": "Escolha a opção que melhor descreve o motivo da procura.",
        "options": [
            {"code": "mal_estar", "label": "Estou passando mal"},
            {"code": "dor", "label": "Estou sentindo dor"},
            {"code": "acidente", "label": "Sofri um acidente"},
            {"code": "ferimento", "label": "Estou com algum ferimento"},
            {"code": "exame", "label": "Preciso de um exame"},
            {"code": "medicamento", "label": "Preciso de medicamento ou receita"},
            {"code": "consulta", "label": "Preciso de uma consulta"},
            {"code": "acompanhando", "label": "Estou acompanhando outra pessoa"},
            {"code": "emergencia", "label": "É uma situação de emergência"},
            {"code": "outro", "label": "Outro motivo"},
        ],
    },
    {
        "external_id": "description",
        "text": "Descreva briefly o que está acontecendo (opcional).",
        "type": "text",
        "required": False,
        "order": 2,
        "help_text": "Não inclua dados pessoais. Esta descrição ajuda a orientar o atendimento.",
    },
    {
        "external_id": "dor_regiao",
        "text": "Onde dói?",
        "type": "body_region",
        "required": False,
        "order": 3,
        "conditional_logic": {"show_if": {"question": "reason", "eq": "dor"}},
        "options": [
            {"code": "cabeca", "label": "Cabeça"},
            {"code": "peito", "label": "Peito"},
            {"code": "barriga", "label": "Barriga"},
            {"code": "costas", "label": "Costas"},
            {"code": "bracos_pernas", "label": "Braços ou pernas"},
            {"code": "outro", "label": "Outra região"},
        ],
    },
    {
        "external_id": "dor_intensidade",
        "text": "De 0 a 10, qual a intensidade da dor?",
        "type": "scale",
        "required": False,
        "order": 4,
        "conditional_logic": {"show_if": {"question": "reason", "eq": "dor"}},
        "options": [{"code": str(i), "label": str(i)} for i in range(0, 11)],
    },
    {
        "external_id": "dor_toracica",
        "text": "A dor é no peito ou parece pressão/falta de ar?",
        "type": "boolean",
        "required": False,
        "order": 5,
        "conditional_logic": {"show_if": {"any": [{"question": "reason", "eq": "dor"}, {"question": "reason", "eq": "mal_estar"}]}},
        "alert_flags": [{"flag": "chest_emergency", "when": {"eq": True}}],
        "options": [{"code": "true", "label": "Sim"}, {"code": "false", "label": "Não"}],
    },
    {
        "external_id": "dificuldade_respirar",
        "text": "Há dificuldade para respirar?",
        "type": "boolean",
        "required": False,
        "order": 6,
        "conditional_logic": {"show_if": {"any": [{"question": "reason", "eq": "mal_estar"}, {"question": "reason", "eq": "dor"}, {"question": "reason", "eq": "emergencia"}]}},
        "alert_flags": [{"flag": "respiratory_emergency", "when": {"eq": True}}],
        "options": [{"code": "true", "label": "Sim"}, {"code": "false", "label": "Não"}],
    },
    {
        "external_id": "febre",
        "text": "Há febre?",
        "type": "boolean",
        "required": False,
        "order": 7,
        "conditional_logic": {"show_if": {"any": [{"question": "reason", "eq": "mal_estar"}, {"question": "reason", "eq": "dor"}, {"question": "reason", "eq": "acompanhando"}]}},
        "alert_flags": [{"flag": "fever", "when": {"eq": True}}],
        "options": [{"code": "true", "label": "Sim"}, {"code": "false", "label": "Não"}],
    },
    {
        "external_id": "febre_temperatura",
        "text": "Se souber, qual a temperatura (°C)?",
        "type": "scale",
        "required": False,
        "order": 8,
        "conditional_logic": {"show_if": {"question": "febre", "eq": True}},
        "alert_flags": [{"flag": "high_fever", "when": {"gte": 39}}],
        "options": [{"code": str(t), "label": f"{t} °C"} for t in range(35, 42)],
    },
    {
        "external_id": "vomitos",
        "text": "Há vômitos persistentes?",
        "type": "boolean",
        "required": False,
        "order": 9,
        "conditional_logic": {"show_if": {"question": "reason", "eq": "mal_estar"}},
        "options": [{"code": "true", "label": "Sim"}, {"code": "false", "label": "Não"}],
    },
    {
        "external_id": "consciencia",
        "text": "A pessoa está consciente?",
        "type": "boolean",
        "required": False,
        "order": 10,
        "conditional_logic": {"show_if": {"any": [{"question": "reason", "eq": "acidente"}, {"question": "reason", "eq": "ferimento"}, {"question": "reason", "eq": "emergencia"}, {"question": "reason", "eq": "mal_estar"}]}},
        "alert_flags": [{"flag": "loss_of_consciousness", "when": {"eq": False}}],
        "options": [{"code": "true", "label": "Sim"}, {"code": "false", "label": "Não"}],
    },
    {
        "external_id": "respiracao",
        "text": "A pessoa está respirando normalmente?",
        "type": "boolean",
        "required": False,
        "order": 11,
        "conditional_logic": {"show_if": {"any": [{"question": "reason", "eq": "acidente"}, {"question": "reason", "eq": "ferimento"}, {"question": "reason", "eq": "emergencia"}, {"question": "reason", "eq": "mal_estar"}]}},
        "alert_flags": [{"flag": "respiratory_emergency", "when": {"eq": False}}],
        "options": [{"code": "true", "label": "Sim"}, {"code": "false", "label": "Não"}],
    },
    {
        "external_id": "sangramento",
        "text": "Há sangramento?",
        "type": "boolean",
        "required": False,
        "order": 12,
        "conditional_logic": {"show_if": {"any": [{"question": "reason", "eq": "ferimento"}, {"question": "reason", "eq": "acidente"}]}},
        "options": [{"code": "true", "label": "Sim"}, {"code": "false", "label": "Não"}],
    },
    {
        "external_id": "sangramento_intenso",
        "text": "O sangramento é intenso (não para com pressão)?",
        "type": "boolean",
        "required": False,
        "order": 13,
        "conditional_logic": {"show_if": {"question": "sangramento", "eq": True}},
        "alert_flags": [{"flag": "severe_bleeding", "when": {"eq": True}}],
        "options": [{"code": "true", "label": "Sim"}, {"code": "false", "label": "Não"}],
    },
    {
        "external_id": "causa_ferimento",
        "text": "O que causou o ferimento?",
        "type": "single_choice",
        "required": False,
        "order": 14,
        "conditional_logic": {"show_if": {"question": "reason", "eq": "ferimento"}},
        "options": [
            {"code": "corte", "label": "Corte com objeto comum"},
            {"code": "arma_branca", "label": "Ferimento por arma branca", "alert_flag": "weapon_injury"},
            {"code": "arma_fogo", "label": "Ferimento por arma de fogo", "alert_flag": "weapon_injury"},
            {"code": "queimadura", "label": "Queimadura"},
            {"code": "queda", "label": "Queda"},
            {"code": "outro", "label": "Outro"},
        ],
    },
    {
        "external_id": "tipo_acidente",
        "text": "Que tipo de acidente?",
        "type": "single_choice",
        "required": False,
        "order": 15,
        "conditional_logic": {"show_if": {"question": "reason", "eq": "acidente"}},
        "options": [
            {"code": "transito", "label": "Acidente de trânsito"},
            {"code": "domestico", "label": "Acidente doméstico"},
            {"code": "trabalho", "label": "Acidente de trabalho"},
            {"code": "queda", "label": "Queda"},
            {"code": "outro", "label": "Outro"},
        ],
    },
    {
        "external_id": "convulsao",
        "text": "Houve convulsão?",
        "type": "boolean",
        "required": False,
        "order": 16,
        "conditional_logic": {"show_if": {"any": [{"question": "reason", "eq": "mal_estar"}, {"question": "reason", "eq": "emergencia"}]}},
        "alert_flags": [{"flag": "seizure", "when": {"eq": True}}],
        "options": [{"code": "true", "label": "Sim"}, {"code": "false", "label": "Não"}],
    },
    {
        "external_id": "sinais_avc",
        "text": "Há fraqueza ou formigamento em um lado do corpo?",
        "type": "boolean",
        "required": False,
        "order": 17,
        "conditional_logic": {"show_if": {"any": [{"question": "reason", "eq": "mal_estar"}, {"question": "reason", "eq": "dor"}]}},
        "alert_flags": [{"flag": "stroke", "when": {"eq": True}}],
        "options": [{"code": "true", "label": "Sim"}, {"code": "false", "label": "Não"}],
    },
]


def _seed_questionnaire(db: Session) -> QuestionnaireVersion:
    questionnaire = Questionnaire(
        name="Questionário inteligente de pré-atendimento",
        description="Formulário dinâmico e conservador para orientação de acesso. Demonstrativo.",
        current_version=1,
        is_active=True,
    )
    db.add(questionnaire)
    db.flush()
    version = QuestionnaireVersion(
        questionnaire_id=questionnaire.id,
        version=1,
        status="published",
        rule_set_version=RULE_SET_VERSION,
    )
    db.add(version)
    db.flush()

    for spec in _QUESTIONS:
        question = Question(
            version_id=version.id,
            external_id=spec["external_id"],
            text=spec["text"],
            type=spec["type"],
            required=spec.get("required", False),
            order_index=spec["order"],
            conditional_logic=spec.get("conditional_logic"),
            alert_flags=spec.get("alert_flags"),
            help_text=spec.get("help_text"),
        )
        db.add(question)
        db.flush()
        for index, option in enumerate(spec.get("options", [])):
            db.add(
                QuestionOption(
                    question_id=question.id,
                    code=option["code"],
                    label=option["label"],
                    order_index=index,
                    alert_flag=option.get("alert_flag"),
                )
            )
    db.commit()
    return version


def _seed_rules(db: Session) -> int:
    rules = [
        {
            "name": "emergencia_grave",
            "description": "Sinais de possível emergência (armas, inconsciência, respiração, sangramento intenso, convulsão, AVC, dor torácica).",
            "priority": 10,
            "category": "D",
            "service_hint": "emergencia",
            "conditions": {
                "any": [
                    {"question": "reason", "eq": "emergencia"},
                    {"question": "causa_ferimento", "in": ["arma_branca", "arma_fogo"]},
                    {"question": "consciencia", "eq": False},
                    {"question": "respiracao", "eq": False},
                    {"question": "sangramento_intenso", "eq": True},
                    {"question": "convulsao", "eq": True},
                    {"question": "sinais_avc", "eq": True},
                    {"question": "dor_toracica", "eq": True},
                    {"question": "dificuldade_respirar", "eq": True},
                ]
            },
            "alert_flags": ["possible_emergency"],
            "confidence": 0.9,
            "stop_flow": True,
            "needs_professional": True,
            "message_template": (
                "O relato indica possível emergência. Interrompemos o pré-cadastro: "
                "procure socorro imediato ligando para o SAMU 192."
            ),
        },
        {
            "name": "possivel_necessidade_hospitalar",
            "description": "Traumas e dores intensas que podem precisar de recursos hospitalares.",
            "priority": 20,
            "category": "C",
            "service_hint": "hospital",
            "conditions": {
                "any": [
                    {"question": "tipo_acidente", "in": ["transito", "trabalho"]},
                    {"question": "dor_intensidade", "gte": 8},
                    {"all": [{"question": "febre", "eq": True}, {"question": "febre_temperatura", "gte": 39.5}]},
                ]
            },
            "alert_flags": ["possible_hospital_care"],
            "confidence": 0.65,
            "stop_flow": False,
            "needs_professional": True,
            "message_template": (
                "Pelo relato, pode ser necessária avaliação com recursos hospitalares. "
                "A indicação é orientativa e não substitui a regulação médica."
            ),
        },
        {
            "name": "possivel_atendimento_upa",
            "description": "Queixas agudas sem sinais de emergência identificados.",
            "priority": 30,
            "category": "B",
            "service_hint": "upa",
            "conditions": {
                "any": [
                    {"question": "reason", "in": ["mal_estar", "dor", "ferimento", "acidente", "acompanhando"]},
                    {"question": "febre", "eq": True},
                    {"question": "vomitos", "eq": True},
                ]
            },
            "alert_flags": [],
            "confidence": 0.6,
            "stop_flow": False,
            "needs_professional": True,
            "message_template": (
                "Com base nas informações, uma UPA pode ser adequada para avaliação. "
                "A prioridade será definida por profissionais de saúde."
            ),
        },
        {
            "name": "atencao_basica",
            "description": "Demandas não urgentes: consulta de rotina, receita, exame.",
            "priority": 40,
            "category": "A",
            "service_hint": "atencao_basica",
            "conditions": {
                "any": [
                    {"question": "reason", "in": ["consulta", "medicamento", "exame", "outro"]},
                ]
            },
            "alert_flags": [],
            "confidence": 0.7,
            "stop_flow": False,
            "needs_professional": False,
            "message_template": (
                "Para esta necessidade, a atenção básica (UBS) costuma ser o caminho mais adequado. "
                "Procure a UBS mais próxima."
            ),
        },
    ]
    for spec in rules:
        db.add(
            GuidanceRule(
                rule_set_version=RULE_SET_VERSION,
                name=spec["name"],
                description=spec["description"],
                priority=spec["priority"],
                category=spec["category"],
                service_hint=spec["service_hint"],
                conditions=spec["conditions"],
                alert_flags=spec["alert_flags"],
                confidence=spec["confidence"],
                stop_flow=spec["stop_flow"],
                needs_professional=spec["needs_professional"],
                message_template=spec["message_template"],
                is_active=True,
            )
        )
    db.commit()
    return len(rules)


def _seed_history(db: Session, units: Dict[str, str]) -> None:
    """Histórico simulado para alimentar as estimativas (UPA Centro e UPA Norte)."""
    now = datetime.now(timezone.utc)
    durations_centro = [18, 20, 22, 25, 26, 28, 30, 30, 32, 34, 35, 40]
    for index, duration in enumerate(durations_centro):
        _create_finished_request(
            db,
            units["upa_centro"],
            f"Paciente Simulado {index + 1}",
            now - timedelta(days=index % 10, hours=index + 1),
            duration,
        )
    for index, duration in enumerate([22, 26, 31]):
        _create_finished_request(
            db,
            units["upa_norte"],
            f"Paciente Norte {index + 1}",
            now - timedelta(days=index + 1),
            duration,
        )
    # solicitações atuais aguardando (alimentam a fila e a estimativa)
    for index in range(2):
        _create_waiting_request(db, units["upa_centro"], f"Aguardando Centro {index + 1}")
    for index in range(4):
        _create_waiting_request(db, units["upa_norte"], f"Aguardando Norte {index + 1}")


def _create_finished_request(db: Session, unit_id: str, name: str, when: datetime, duration: int):
    request = request_repo.create_request(
        db,
        {
            "submission_id": None,
            "patient_name": name,
            "patient_phone": "(11) 90000-0000",
            "unit_id": unit_id,
            "category": "B",
            "complaint_summary": "Atendimento simulado para histórico de estimativas.",
            "status": "sent",
        },
    )
    request_repo.update_status(db, request, "in_care", None, "Simulação")
    attendance = queue_repo.create_attendance(db, request.id, unit_id, when)
    queue_repo.finish_attendance(
        db, attendance, when + timedelta(minutes=duration), outcome="released"
    )
    request_repo.update_status(db, request, "finished", None, "Simulação")
    ticket = queue_repo.get_ticket_for_request(db, request.id)
    if ticket:
        queue_repo.update_ticket(db, ticket, "done", note="Simulação concluída")


def _create_waiting_request(db: Session, unit_id: str, name: str):
    request = request_repo.create_request(
        db,
        {
            "submission_id": None,
            "patient_name": name,
            "patient_phone": "(11) 90000-0000",
            "unit_id": unit_id,
            "category": "B",
            "complaint_summary": "Solicitação simulada aguardando.",
            "status": "sent",
        },
    )
    request_repo.update_status(db, request, "awaiting_confirmation", None, "Simulação")


def _seed_alert(db: Session, units: Dict[str, str], patient: Optional[User]) -> None:
    alert = alert_repo.create_alert(
        db,
        {
            "alert_code": "ALERT-DEMO01",
            "reporter_user_id": patient.id if patient else None,
            "destination_unit_id": units["hospital"],
            "description": "Paciente simulado a caminho com dor torácica. Dados não verificados clinicamente.",
            "occurred_at": datetime.now(timezone.utc) - timedelta(minutes=12),
            "patient_conscious": "yes",
            "patient_breathing": "yes",
            "bleeding": "no",
            "current_situation": "Estável, acompanhado por familiar.",
            "eta_minutes": 20,
            "alert_flags": ["patient_on_the_way"],
        },
    )
    alert_repo.update_alert(db, alert, "confirmed", None, "Recebimento confirmado pela equipe")


def run() -> Dict[str, Any]:
    init_db()
    db = SessionLocal()
    try:
        stats = seed(db)
        return stats
    finally:
        db.close()


if __name__ == "__main__":
    result = run()
    print(result)
