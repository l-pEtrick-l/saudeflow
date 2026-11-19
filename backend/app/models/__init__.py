"""Registro central dos modelos (necessário para o SQLAlchemy mapear tudo)."""

from app.models.alert import EmergencyAlert, EmergencyAlertEvent
from app.models.audit import AuditLog
from app.models.estimate import WaitEstimate
from app.models.guidance import GuidanceResult, GuidanceRule
from app.models.integration import (
    ExternalUnit,
    IntegrationSetting,
    IntegrationSource,
    SyncLog,
)
from app.models.notification import Notification
from app.models.questionnaire import (
    Question,
    QuestionOption,
    Questionnaire,
    QuestionnaireAnswer,
    QuestionnaireSubmission,
    QuestionnaireVersion,
)
from app.models.queue import Attendance, CheckIn, QueueEvent, QueueTicket
from app.models.request import CareRequest, ProtocolCounter, RequestEvent
from app.models.unit import (
    CapacitySnapshot,
    HealthcareUnit,
    HealthcareUnitService,
    UnitStaff,
)
from app.models.user import Permission, Role, RolePermission, User, UserRole

__all__ = [
    "Role",
    "Permission",
    "RolePermission",
    "User",
    "UserRole",
    "HealthcareUnit",
    "HealthcareUnitService",
    "UnitStaff",
    "CapacitySnapshot",
    "Questionnaire",
    "QuestionnaireVersion",
    "Question",
    "QuestionOption",
    "QuestionnaireSubmission",
    "QuestionnaireAnswer",
    "GuidanceRule",
    "GuidanceResult",
    "CareRequest",
    "RequestEvent",
    "ProtocolCounter",
    "QueueTicket",
    "QueueEvent",
    "CheckIn",
    "Attendance",
    "WaitEstimate",
    "EmergencyAlert",
    "EmergencyAlertEvent",
    "Notification",
    "AuditLog",
    "IntegrationSource",
    "ExternalUnit",
    "SyncLog",
    "IntegrationSetting",
]
