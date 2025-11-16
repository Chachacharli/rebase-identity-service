from typing import List, Optional
from uuid import UUID

from fastapi import Query
from pydantic import BaseModel

from app.core.filtering.filters import Order
from app.schemas.role import RoleReadWithoutPermissions


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserRead(BaseModel):
    id: UUID
    username: str
    email: str

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    username: Optional[str]
    email: Optional[str]
    password: Optional[str]


class UserSetRole(BaseModel):
    id: UUID
    role_id: UUID


class UserWithRoles(UserRead):
    roles: List[RoleReadWithoutPermissions] = []


class UserFilters(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    order_by: Optional[str] = Query(None)
    order_dir: Order = Query(Order.none)
