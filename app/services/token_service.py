import secrets
from dataclasses import dataclass
from datetime import timedelta, timezone

from sqlmodel import Session

from app.models.access_token import AccessToken
from app.models.refresh_token import RefreshToken
from app.repositories.access_token_repository import AccessTokenRepository
from app.repositories.app_settings_repository import AppSettingRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.utils.dates import generate_date_now, generate_expiration


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int

    def to_dict(self):
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_in": self.expires_in,
        }


class TokenService:
    def __init__(self, session: Session):
        self.session = session
        self.rt_repo = RefreshTokenRepository(session)
        self.at_repo = AccessTokenRepository(session)
        self.app_settings_repo = AppSettingRepository(session)

    def _now(self):
        return generate_date_now()

    def create_refresh_token(self, rt: RefreshToken) -> RefreshToken:
        """Create and store a new refresh token."""
        new_token = self.rt_repo.create(rt)
        return new_token

    def create_access_token(self, at: AccessToken) -> AccessToken:
        """Create and store a new access token."""
        new_token = self.at_repo.create(at)
        return new_token

    def issue_tokens(self, user_id, client_id, scope) -> TokenPair:
        now = self._now()
        access_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(48)

        ttl_access = int(self.app_settings_repo.get("ttl_access_token", 1800))
        ttl_refresh = int(self.app_settings_repo.get("ttl_refresh_token", 604800))

        rt = RefreshToken(
            token=refresh_token,
            user_id=user_id,
            client_id=client_id,
            scope=scope,
            expires_at=now + timedelta(minutes=ttl_refresh),
            revoked=False,
        )

        # Refresh token
        new_rt = self.rt_repo.create(rt)

        at_token = AccessToken(
            token=access_token,
            user_id=user_id,
            client_id=client_id,
            scope=scope,
            expires_at=now + timedelta(minutes=ttl_access),
            revoked=False,
            refresh_token_id=new_rt.id,
        )

        # Access token
        self.at_repo.create(at_token)

        # TODO: Return additional info (token type, scope, etc)
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ttl_access,
        )

    def refresh_with_rotation(
        self, refresh_token_str: str, client_id: str
    ) -> TokenPair:
        """Usa refresh token para emitir nuevo access + rotar refresh token.
        Detecta reuse si refresh token ya fue revocado.
        """
        now = self._now()
        rt = self.rt_repo.get(refresh_token_str)

        ttl_access = int(self.app_settings_repo.get("ttl_access_token", 1800))
        ttl_refresh = int(self.app_settings_repo.get("ttl_refresh_token", 604800))

        if not rt:
            # token desconocido -> posible reuse o ataque: no devolver detalle
            raise ValueError("invalid_grant")

        # Si el refresh token está revocado -> reuse detection
        if rt.revoked:
            # reutilización detectada: revocar cadena completa asociada a este lineage
            self.rt_repo.revoke_chain(rt)
            # revocar accesos derivados
            self.at_repo.revoke_by_refresh(rt.id)
            raise ValueError("Token revoked")

        # Si expiró
        # TODO: Fix `TypeError: can't compare offset-naive and offset-aware datetimes`
        exp = rt.expires_at.replace(tzinfo=timezone.utc)
        if exp < now:
            raise ValueError("Your token has been expired")

        # Validar que el client_id coincide
        if str(rt.client_id) != str(client_id):
            raise ValueError("Invalid client")

        # ROTACIÓN: crear nuevo refresh token y marcar reemplazo
        new_refresh_token_str = secrets.token_urlsafe(48)
        new_rt = RefreshToken(
            token=new_refresh_token_str,
            user_id=rt.user_id,
            client_id=rt.client_id,
            scope=rt.scope,
            expires_at=generate_expiration(ttl_refresh),
            revoked=False,
            created_at=now,
            parent_id=rt.id,
            replaced_by=None,
        )

        rt_repsonse = self.rt_repo.create(new_rt)

        # crear nuevo access token ligado al rt_repsonse
        new_access_token_str = secrets.token_urlsafe(32)

        new_at = AccessToken(
            token=new_access_token_str,
            user_id=rt.user_id,
            client_id=rt.client_id,
            scope=rt.scope,
            expires_at=generate_expiration(ttl_access),
            refresh_token_id=rt_repsonse.id,
            revoked=False,
        )

        # Revoke old token and generate new one
        self.at_repo.revoke_by_refresh(rt.id)
        self.at_repo.create(new_at)

        # Marcar el antiguo como reemplazado (revocar)
        self.rt_repo.mark_replaced(rt, new_rt)

        # TODO: Return additional info (token type, scope, etc)
        return TokenPair(
            access_token=new_access_token_str,
            refresh_token=new_refresh_token_str,
            expires_in=ttl_access,
        )

    def revoke_token(self, token_str: str) -> None:
        """Revoke token opaco (access o refresh)."""
        at = self.at_repo.get(token_str)
        rt_id = None
        rt = None
        if at:
            self.at_repo.revoke(at)
            rt_id = at.refresh_token_id
            rt = self.rt_repo.get_by_id(str(rt_id))

        if rt:
            # revocar cadena (refresh y descendientes) y sus access tokens
            self.rt_repo.revoke_chain(rt)
            self.at_repo.revoke_by_refresh(rt.id)
            return

        # token desconocido -> ok (es idempotente según RFC)
        return

    def issue_client_token(self, client_id, scope) -> TokenPair:
        now = self._now()

        access_token = secrets.token_urlsafe(32)

        ttl_access = int(self.app_settings_repo.get("ttl_access_token", 1800))

        at = AccessToken(
            token=access_token,
            user_id=None,
            client_id=client_id,
            scope=scope,
            expires_at=now + timedelta(minutes=ttl_access),
            revoked=False,
            refresh_token_id=None,
        )

        self.at_repo.create(at)

        return TokenPair(
            access_token=access_token,
            refresh_token=None,
            expires_in=ttl_access,
        )
