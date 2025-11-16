from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page, paginate
from sqlmodel import Session

from app.core.db import get_session
from app.schemas.user import (
    UserCreate,
    UserFilters,
    UserRead,
    UserSetRole,
    UserUpdate,
    UserWithRoles,
)
from app.services.password_service import PasswordService
from app.services.user_service import UserService

router = APIRouter(prefix="/v1/user")


@router.post(
    "/",
    response_model=UserRead,
)
def create_user(user: UserCreate, db: Session = Depends(get_session)):
    user_service = UserService(db)
    created_user = user_service.create_user(
        email=user.email, password=user.password, username=user.username
    )

    new_user = UserRead(
        email=created_user.email, id=created_user.id, username=created_user.username
    )

    return new_user


@router.get("/{user_id}", response_model=UserWithRoles)
def get_user(user_id: UUID, db: Session = Depends(get_session)) -> UserWithRoles:
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserWithRoles.model_validate(user)


@router.get("/", response_model=Page[UserRead])
def list_users(db: Session = Depends(get_session), filters=Depends(UserFilters)):
    user_service = UserService(db)
    users = user_service.get_all_users(filters)
    return paginate([UserRead.model_validate(user) for user in users])


@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: UUID, user_update: UserUpdate, db: Session = Depends(get_session)
):
    # TODO: implement update logic
    pass


@router.delete("/{user_id}")
def delete_user(user_id: UUID, db: Session = Depends(get_session)):
    # TODO: implemente soft delete logic
    pass


@router.post("/set_role")
def set_user_role(
    user_set_roles: UserSetRole, db: Session = Depends(get_session)
) -> UserWithRoles:
    user_service = UserService(db)
    updated_user = user_service.set_user_role(user_set_roles)
    return UserWithRoles.model_validate(updated_user)


@router.post("/remove_role")
def remove_user_role(
    user_set_roles: UserSetRole, db: Session = Depends(get_session)
) -> UserWithRoles:
    user_service = UserService(db)
    updated_user = user_service.remove_user_role(user_set_roles)
    return UserWithRoles.model_validate(updated_user)


@router.get("test")
def test_endpoint(db: Session = Depends(get_session)):
    password_service = PasswordService("secret")
    token = password_service.generate_token("test@example.com")
    token_valid = password_service.verify_token(
        "InRjY2FfZWRuc0Bob3RtYWlsLmNvbSI.aRegog.ckrDzqd_zsvRCwYUkf7Cf2miMow"
    )

    return {"token": token, "token_valid": token_valid}
