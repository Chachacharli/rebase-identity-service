from fastapi import status

from .base import AppException
from .exception_codes import ExceptionCode


class TokenExpiredException(AppException):
    def __init__(self, message="Token expired", details=None):
        super().__init__(
            message=message,
            code=ExceptionCode.UNAUTHORIZED,
            http_status=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class InvalidPasswordException(AppException):
    def __init__(self, message="Invalid password", details=None):
        super().__init__(
            message=message,
            code=ExceptionCode.INVALID_PASSWORD,
            http_status=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class UserNameAlreadyExistsException(AppException):
    def __init__(self, message="Username already exists", details=None):
        super().__init__(
            message=message,
            code=ExceptionCode.USERNAME_ALREADY_EXISTS,
            http_status=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class EmailAlreadyExistsException(AppException):
    def __init__(self, message="Email already exists", details=None):
        super().__init__(
            message=message,
            code=ExceptionCode.EMAIL_ALREADY_EXISTS,
            http_status=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class InvalidUsernameException(AppException):
    def __init__(self, message="Invalid username", details=None):
        super().__init__(
            message=message,
            code=ExceptionCode.VALIDATION_ERROR,
            http_status=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class InvalidUsernameOrPasswordException(AppException):
    def __init__(self, message="Invalid username or password", details=None):
        super().__init__(
            message=message,
            code=ExceptionCode.UNAUTHORIZED,
            http_status=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class RequiredRoleException(AppException):
    def __init__(self, required_role, details=None):
        super().__init__(
            message=f"Role '{required_role}' required",
            code=ExceptionCode.ROLE_REQUIRED,
            http_status=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class RequiredPermissionException(AppException):
    def __init__(self, required_permission, details=None):
        super().__init__(
            message=f"Permission '{required_permission}' required",
            code=ExceptionCode.PERMISSION_REQUIRED,
            http_status=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class UserEmailNotVerifiedException(AppException):
    def __init__(
        self,
        message="User email not verified, please verify your email checking your inbox",
        details=None,
    ):
        super().__init__(
            message=message,
            code=ExceptionCode.EMAIL_NOT_VERIFIED,
            http_status=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class UserAccountLockedException(AppException):
    def __init__(
        self,
        message="User account locked due to too many failed login attempts. Please try again later.",
        details=None,
    ):
        super().__init__(
            message=message,
            code=ExceptionCode.ACCOUNT_LOCKED
            if hasattr(ExceptionCode, "ACCOUNT_LOCKED")
            else ExceptionCode.UNAUTHORIZED,
            http_status=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class UnauthorizedClientException(AppException):
    def __init__(self, message="Unauthorized client", details=None):
        super().__init__(
            message=message,
            code=ExceptionCode.UNAUTHORIZED_CLIENT,
            http_status=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class ScopesNotAllowedException(AppException):
    def __init__(self, message="Requested scopes are not allowed", details=None):
        super().__init__(
            message=message,
            code=ExceptionCode.FORBIDDEN,
            http_status=status.HTTP_403_FORBIDDEN,
            details=details,
        )
