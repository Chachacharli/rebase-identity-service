from passlib.hash import pbkdf2_sha256
from sqlmodel import Session, select

from app.components.user.user_manager import UserManager
from app.exceptions.bussiness_exceptions import (
    InvalidUsernameOrPasswordException,
    UserEmailNotVerifiedException,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserFilters, UserSetRole
from app.schemas.user_info_schema import UserInfoSchema


class UserService:
    def __init__(self, session: Session):
        self.session = session
        self.user_repo = UserRepository(session)

    def get_all_users(self, filters: UserFilters) -> list[User]:
        user_repository = UserRepository(self.session)
        users = user_repository.get_users(filters)

        return users

    def create_user(self, username: str, email: str, password: str) -> User:
        user_repository = UserRepository(self.session)
        user_manager = UserManager(user_repository)

        created_user = user_manager.create_user(username, password, email)
        return created_user

    def authenticate_user(self, username: str, password: str) -> User | None:
        user = self.user_repo.get_by_username(username)
        if user and pbkdf2_sha256.verify(password, user.password):
            return user
        return None

    def authenticate_user_by_email_or_username(
        self, email_or_username: str, password: str
    ) -> User:
        user_manager = UserManager(self.user_repo)
        user = self.user_repo.get_by_email_or_username(email_or_username)
        if not user:
            raise InvalidUsernameOrPasswordException()

        # Validate credentials (this will increment attempts on failure and reset on success)
        is_valid = user_manager.validate_user_credentials(user, password)

        if not is_valid:
            raise InvalidUsernameOrPasswordException()

        # Credentials valid — now ensure the user's email is verified
        if user.email_verified is False:
            raise UserEmailNotVerifiedException()

        return user

    def reset_password(self, new_password: str, token: str) -> User:
        user_manager = UserManager(self.user_repo)
        response = user_manager.reset_password(new_password, token)
        return response

    def verify_email(self, token: str) -> bool:
        """Verifies an email using the provided token."""
        user_manager = UserManager(self.user_repo)
        return user_manager.verify_email(token)

    def resend_verification(self, email: str) -> bool:
        """Resend verification email to the given address if user exists and not verified."""
        user = self.user_repo.get_by_email(email)
        if not user:
            return False
        if user.email_verified:
            return False

        user_manager = UserManager(self.user_repo)
        try:
            user_manager.send_verification_email(email)
            return True
        except Exception:
            return False

    def get_user_by_id(self, user_id: str) -> User | None:
        user = self.user_repo.get_by_id(user_id)
        return user

    def set_user_role(self, user_role: UserSetRole) -> User | None:
        user_repo = UserRepository(self.session)
        user_set_role = UserSetRole(id=user_role.id, role_id=user_role.role_id)
        updated_user = user_repo.set_role(user_set_role)
        return updated_user

    def remove_user_role(self, user_role: UserSetRole) -> User | None:
        user_repo = UserRepository(self.session)
        user_set_role = UserSetRole(id=user_role.id, role_id=user_role.role_id)
        updated_user = user_repo.remove_role(user_set_role)
        return updated_user

    def send_mail_reset_password(self, email: str) -> bool:
        user_manager = UserManager(self.user_repo)
        response = user_manager.send_mail_reset_password(email)
        return response

    def get_userinfo(self, user_id: str) -> UserInfoSchema | None:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return None
        return UserInfoSchema(
            sub=str(user.id),
            username=user.username,
            email=user.email,
            email_verified=user.email_verified,
        )
