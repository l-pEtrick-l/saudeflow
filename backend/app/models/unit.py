from app.database import Base
from app.utils import new_uuid
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
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


class HealthcareUnit(Base, TimestampMixin):
    __tablename__ = "healthcare_units"

    id = Column(String(36), primary_key=True, default=new_uuid)
    name = Column(String(200), nullable=False, index=True)
    type = Column(String(20), nullable=False, index=True)  # ubs | upa | hospital | emergency
    cnes_code = Column(String(20), unique=True, index=True)
    source = Column(String(20), default="manual", nullable=False)  # manual | cnes | datasus
    is_simulated = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    street = Column(String(255))
    number = Column(String(20))
    complement = Column(String(120))
    neighborhood = Column(String(120))
    city = Column(String(120), index=True)
    state = Column(String(2), index=True)
    postal_code = Column(String(10))
    latitude = Column(Float)
    longitude = Column(Float)

    phone = Column(String(30))
    email = Column(String(200))

    deleted_at = Column(DateTime(timezone=True))

    services = relationship(
        "HealthcareUnitService",
        back_populates="unit",
        cascade="all, delete-orphan",
    )

    @property
    def is_emergency(self) -> bool:
        return self.type in ("upa", "hospital", "emergency")


class HealthcareUnitService(Base):
    __tablename__ = "healthcare_unit_services"

    id = Column(String(36), primary_key=True, default=new_uuid)
    unit_id = Column(
        String(36), ForeignKey("healthcare_units.id", ondelete="CASCADE"), nullable=False, index=True
    )
    service_code = Column(String(50), nullable=False)
    service_name = Column(String(150), nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    notes = Column(Text)

    unit = relationship("HealthcareUnit", back_populates="services")


class UnitStaff(Base, TimestampMixin):
    __tablename__ = "unit_staff"
    __table_args__ = (UniqueConstraint("unit_id", "user_id", "role", name="uq_unit_staff"),)

    id = Column(String(36), primary_key=True, default=new_uuid)
    unit_id = Column(
        String(36), ForeignKey("healthcare_units.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(30), nullable=False)  # manager | receptionist | classifier | operator
    is_active = Column(Boolean, default=True, nullable=False)


class CapacitySnapshot(Base):
    __tablename__ = "capacity_snapshots"

    id = Column(String(36), primary_key=True, default=new_uuid)
    unit_id = Column(
        String(36), ForeignKey("healthcare_units.id", ondelete="CASCADE"), nullable=False, index=True
    )
    professionals_available = Column(Integer, default=0, nullable=False)
    rooms_active = Column(Integer, default=0, nullable=False)
    welcome_capacity = Column(Integer, default=0, nullable=False)
    services_unavailable = Column(JSON, default=list)
    receiving_pre_registrations = Column(Boolean, default=True, nullable=False)
    exceptional_status = Column(String(50))
    notes = Column(Text)
    created_by = Column(String(36))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
