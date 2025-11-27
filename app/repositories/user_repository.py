from datetime import datetime, timezone

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.core.filtering.filter_builder import FilterBuilder
from app.exceptions.http_exceptions import NotFoundException
from app.models.role import Role
from app.models.user import User
from app.schemas.user import UserFilters, UserSetRole


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_users(self, filters: UserFilters) -> list[User]:
        filter_builder = FilterBuilder(User)
        statement = select(User)
        filter_builder.text("username", filters.username)
        filter_builder.text("email", filters.email)
        filter_builder.order_by(filters.order_by, filters.order_dir)

        statement = filter_builder.build(statement)
        res = self.session.exec(statement)

        return res.all()

    def get_by_username(self, username: str):
        return self.session.exec(select(User).where(User.username == username)).first()

    def get_by_email(self, email: str):
        return self.session.exec(select(User).where(User.email == email)).first()

    def get_by_email_or_username(self, email_or_username: str):
        statement = select(User).where(
            (User.email == email_or_username) | (User.username == email_or_username)
        )
        return self.session.exec(statement).first()

    def get_by_id(self, user_id: str) -> User | None:
        statement = (
            select(User).where(User.id == user_id).options(selectinload(User.roles))
        )
        result = self.session.exec(statement).first()
        return result

    def create(self, user: User):
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def set_role(self, role: UserSetRole):
        user = self.session.get(User, role.id)
        if not user:
            raise NotFoundException(entity="User", entity_id=role.id)

        role_instance = self.session.get(Role, role.role_id)
        if not role_instance:
            raise NotFoundException(entity="Role", entity_id=role.role_id)

        if role_instance in user.roles:
            return user

        user.roles.append(role_instance)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def remove_role(self, role: UserSetRole):
        user = self.session.get(User, role.id)
        if not user:
            raise NotFoundException(entity="User", entity_id=role.id)

        role_instance = self.session.get(Role, role.role_id)
        if not role_instance:
            raise NotFoundException(entity="Role", entity_id=role.role_id)

        if role_instance not in user.roles:
            return user

        user.roles.remove(role_instance)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def change_password(self, user: User, new_password: str):
        if user is None:
            raise NotFoundException(entity="User")

        user.password = new_password
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)

        return user

    def set_email_verified(self, user: User):
        """Mark user's email as verified and persist the change."""
        if user is None:
            raise NotFoundException(entity="User")

        user.email_verified = True
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def increment_login_attempts(self, user: User, increment: int = 1):
        """Increment the user's login_attempts counter and persist."""
        if user is None:
            raise NotFoundException(entity="User")

        user.login_attempts = (user.login_attempts or 0) + increment
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def reset_login_attempts_and_set_last_login(self, user: User):
        """Reset login_attempts to zero and update last_login timestamp."""
        if user is None:
            raise NotFoundException(entity="User")

        user.login_attempts = 0
        user.last_login = datetime.now(timezone.utc)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
