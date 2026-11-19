from app.database import Base
from app.utils import new_uuid
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy import func
from sqlalchemy.orm import relationship


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Questionnaire(Base, TimestampMixin):
    __tablename__ = "questionnaires"

    id = Column(String(36), primary_key=True, default=new_uuid)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    current_version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class QuestionnaireVersion(Base, TimestampMixin):
    __tablename__ = "questionnaire_versions"

    id = Column(String(36), primary_key=True, default=new_uuid)
    questionnaire_id = Column(
        String(36), ForeignKey("questionnaires.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version = Column(Integer, nullable=False)
    status = Column(String(20), default="published", nullable=False)  # draft | published | archived
    rule_set_version = Column(String(50), nullable=False)
    created_by = Column(String(36))

    questions = relationship(
        "Question", back_populates="version", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"

    id = Column(String(36), primary_key=True, default=new_uuid)
    version_id = Column(
        String(36),
        ForeignKey("questionnaire_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_id = Column(String(60), nullable=False, index=True)
    text = Column(Text, nullable=False)
    type = Column(String(30), nullable=False)  # boolean | single_choice | multi_choice | text | scale | body_region | time | number
    required = Column(Boolean, default=False, nullable=False)
    order_index = Column(Integer, default=0, nullable=False)
    conditional_logic = Column(JSON)  # {"show_if": {"question": "...", "in": [...]}}
    alert_flags = Column(JSON)  # [{"flag": "...", "when": {...}}]
    help_text = Column(String(255))

    version = relationship("QuestionnaireVersion", back_populates="questions")
    options = relationship(
        "QuestionOption", back_populates="question", cascade="all, delete-orphan"
    )


class QuestionOption(Base):
    __tablename__ = "question_options"

    id = Column(String(36), primary_key=True, default=new_uuid)
    question_id = Column(
        String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code = Column(String(60), nullable=False)
    label = Column(String(255), nullable=False)
    order_index = Column(Integer, default=0, nullable=False)
    alert_flag = Column(String(60))

    question = relationship("Question", back_populates="options")


class QuestionnaireSubmission(Base, TimestampMixin):
    __tablename__ = "questionnaire_submissions"

    id = Column(String(36), primary_key=True, default=new_uuid)
    version_id = Column(
        String(36),
        ForeignKey("questionnaire_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    session_token = Column(String(36), index=True)
    status = Column(String(20), default="in_progress", nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True))

    answers = relationship(
        "QuestionnaireAnswer",
        back_populates="submission",
        cascade="all, delete-orphan",
    )


class QuestionnaireAnswer(Base):
    __tablename__ = "questionnaire_answers"

    id = Column(String(36), primary_key=True, default=new_uuid)
    submission_id = Column(
        String(36),
        ForeignKey("questionnaire_submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id = Column(
        String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    value_text = Column(Text)
    value_json = Column(JSON)
    answered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    submission = relationship("QuestionnaireSubmission", back_populates="answers")
    question = relationship("Question")
