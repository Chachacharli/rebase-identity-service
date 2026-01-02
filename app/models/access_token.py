import uuid
from datetime import datetime
from typing import List

from sqlmodel import JSON, Column, Field, SQLModel

from app.models.base import PKMixin


class AccessToken(SQLModel, PKMixin, table=True):
    __tablename__ = "access_tokens"
    token: str = Field(index=True, unique=True)
    user_id: uuid.UUID | None = Field(
        default=None, foreign_key="users.id", nullable=True
    )
    client_id: str | None = Field(
        default=None,
        foreign_key="client_applications.client_id",
        nullable=True,
    )
    scope: List[str] = Field(sa_column=Column(JSON))
    expires_at: datetime
    revoked: bool = False
    refresh_token_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="refresh_tokens.id",
        nullable=True,
    )
