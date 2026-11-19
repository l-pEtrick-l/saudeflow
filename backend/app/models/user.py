from app.database import Base
from app.utils import new_uuid
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
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


class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True, default=new_uuid)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255))


class Permission(Base, TimestampMixin):
    __tablename__ = "permissions"

    id = Column(String(36), primary_key=True, default=new_uuid)
    name = Column(String(80), unique=True, nullable=False, index=True)
    description = Column(String(255))


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id = Column(String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(
        String(36), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=new_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=False)
    phone = Column(String(30))
    cpf = Column(String(14), index=True)
    birth_date = Column(Date)
    is_active = Column(Boolean, default=True, nullable=False)
    deleted_at = Column(DateTime(timezone=True))

    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")

    def has_role(self, role_name: str) -> bool:
        return any(ur.role.name == role_name for ur in self.roles)


class UserRole(Base, TimestampMixin):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", "unit_id", name="uq_user_role_unit"),
    )

    id = Column(String(36), primary_key=True, default=new_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    unit_id = Column(String(36), ForeignKey("healthcare_units.id", ondelete="CASCADE"))

    user = relationship("User", back_populates="roles")
    role = relationship("Role")
