from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Protocol
from uuid import UUID

if TYPE_CHECKING:
    # Import for type checking / autocompletion only
    import redis  # type: ignore
else:
    redis = None  # type: ignore

from app.core.config import settings


@dataclass
class AuthorizationCode:
    code: str
    client_id: str
    redirect_uri: str
    code_challenge: str
    user_id: UUID
    expires_at: datetime
    scope: List[str] = field(default_factory=lambda: ["openid email profile"])

    @property
    def is_expired(self) -> bool:
        """Verifica si el código ha expirado."""
        # Ensure timezone-aware comparison: treat naive datetimes as UTC
        now = datetime.now(timezone.utc)
        expires = self.expires_at
        if expires is None:
            return False
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return now > expires


class AuthorizationCodeStoreProtocol(Protocol):
    """Protocol that defines the authorization code store interface."""

    def save(
        self,
        code: str,
        client_id: str,
        redirect_uri: str,
        code_challenge: str,
        user_id: UUID,
        scope: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None,
    ) -> AuthorizationCode: ...

    def validate(self, code: str) -> Optional[AuthorizationCode]: ...


class InMemoryAuthorizationCodeStore:
    """In-memory store for authorization codes.

    This preserves the original behaviour and is used by default. It
    implements the same API used across the codebase so consumers don't
    need to change.
    """

    def __init__(self):
        self._store: Dict[str, AuthorizationCode] = {}

    def save(
        self,
        code: str,
        client_id: str,
        redirect_uri: str,
        code_challenge: str,
        user_id: UUID,
        scope: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None,
    ) -> AuthorizationCode:
        auth_code = AuthorizationCode(
            code=code,
            client_id=client_id,
            redirect_uri=redirect_uri,
            code_challenge=code_challenge,
            user_id=user_id,
            scope=scope or ["openid"],
            expires_at=expires_at,
        )
        self._store[code] = auth_code
        return auth_code

    def validate(self, code: str) -> Optional[AuthorizationCode]:
        auth_code = self._store.get(code)
        if not auth_code:
            return None

        if auth_code.is_expired:
            del self._store[code]
            return None

        # Remove on use (OAuth2 behaviour)
        del self._store[code]
        return auth_code


class RedisAuthorizationCodeStore:
    """Redis-backed store for authorization codes.

    This implementation is optional — it will be used if the environment
    variable `AUTH_CODE_STORE` is set to `redis` and `redis` package is
    installed. If selected but the redis client is not available an
    ImportError is raised to make the problem explicit.
    """

    def __init__(self, redis_url: str):
        # self._client is typed for autocompletion when redis is available
        # Use Any at runtime to avoid import-time dependency issues
        RedisClient: Any
        try:
            import importlib

            redis_mod = importlib.import_module("redis")
            RedisClient = redis_mod.Redis
        except Exception:
            # If redis not available at runtime, raise to let caller handle fallback
            raise

        self._client: "redis.Redis" = RedisClient.from_url(redis_url)  # type: ignore[name-defined]

    def save(
        self,
        code: str,
        client_id: str,
        redirect_uri: str,
        code_challenge: str,
        user_id: UUID,
        scope: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None,
    ) -> AuthorizationCode:
        auth_code = AuthorizationCode(
            code=code,
            client_id=client_id,
            redirect_uri=redirect_uri,
            code_challenge=code_challenge,
            user_id=user_id,
            scope=scope or ["openid"],
            expires_at=expires_at,
        )
        # Store as a simple dict-like payload; Redis TTL should be set based
        # on expires_at if provided.
        payload = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "code_challenge": code_challenge,
            "user_id": str(user_id),
            "scope": ",".join(auth_code.scope),
            # Store UTC timestamp (seconds)
            "expires_at": str(
                int(auth_code.expires_at.astimezone(timezone.utc).timestamp())
            )
            if auth_code.expires_at
            else "",
        }
        # We use hmset and optionally set TTL
        self._client.hset(code, mapping=payload)
        if auth_code.expires_at:
            ttl = int(
                (
                    auth_code.expires_at.astimezone(timezone.utc)
                    - datetime.now(timezone.utc)
                ).total_seconds()
            )
            if ttl > 0:
                self._client.expire(code, ttl)
        return auth_code

    def validate(self, code: str) -> Optional[AuthorizationCode]:
        # hgetall returns Dict[bytes, bytes] when using redis-py
        data_bytes: Dict[bytes, bytes] = self._client.hgetall(code)  # type: ignore[attr-defined]
        if not data_bytes:
            return None
        # convert bytes to str with explicit types for autocompletion
        data: Dict[str, str] = {k.decode(): v.decode() for k, v in data_bytes.items()}
        expires_at: Optional[datetime] = None
        if data.get("expires_at"):
            expires_at = datetime.fromtimestamp(
                int(data["expires_at"]), tz=timezone.utc
            )

        # In Redis we remove the key to enforce single-use
        self._client.delete(code)

        # Build AuthorizationCode object (ensure timezone-aware expires_at)
        if expires_at is not None and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        auth_code = AuthorizationCode(
            code=code,
            client_id=data.get("client_id", ""),
            redirect_uri=data.get("redirect_uri", ""),
            code_challenge=data.get("code_challenge", ""),
            user_id=UUID(data.get("user_id")),
            expires_at=expires_at,
            scope=data.get("scope", "").split(",") if data.get("scope") else [],
        )

        if auth_code.is_expired:
            return None

        return auth_code


# Factory / default selection
_backend = getattr(settings, "AUTH_CODE_STORE", "memory").lower()
if _backend == "redis":
    _redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
    try:
        authorization_code_store: AuthorizationCodeStoreProtocol = (
            RedisAuthorizationCodeStore(_redis_url)
        )
    except Exception:
        # If Redis isn't available fall back to in-memory but warn via stderr.
        # We avoid crashing on import to keep backwards compatibility.
        import sys

        print(
            "Warning: Redis store selected but failed to initialize. Falling back to in-memory store.",
            file=sys.stderr,
        )
        authorization_code_store = InMemoryAuthorizationCodeStore()
else:
    authorization_code_store = InMemoryAuthorizationCodeStore()
