from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from app.models.base import AuditMixin, PKMixin, TimestampMixin
from app.models.user_role import UserRole

if TYPE_CHECKING:
    from app.models.role import Role


class User(SQLModel, PKMixin, TimestampMixin, AuditMixin, table=True):
    __tablename__ = "users"
    # Base fields
    username: str = Field(index=True, unique=True, nullable=False)
    password: str
    email: Optional[str] = Field(default=None, index=True, unique=True)
    is_active: bool = Field(default=True)
    email_verified: bool = Field(default=False)
    login_attempts: int = Field(default=0)
    last_login: Optional[datetime] = Field(default=None)

    # Tenant ID for multi-tenancy support
    tenant_id: Optional[UUID] = Field(default=None, index=True)

    # Relationships
    roles: List["Role"] = Relationship(back_populates="users", link_model=UserRole)
