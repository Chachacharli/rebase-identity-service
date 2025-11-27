import asyncio
from datetime import datetime, timezone

from sqlmodel import Session, delete

from app.core.db import engine
from app.models.access_token import AccessToken
from app.models.refresh_token import RefreshToken


class TokenCleanupService:
    def __init__(self, interval_seconds: int = 300):
        """
        interval_seconds: time interval between cleanup runs in seconds
        """
        self.interval_seconds = interval_seconds
        self._task = None

    async def start(self):
        while True:
            self.cleanup_expired_tokens()
            await asyncio.sleep(self.interval_seconds)

    def cleanup_expired_tokens(self):
        print("[TokenCleanupService] Limpiando tokens expirados...")
        with Session(engine) as session:
            now = datetime.now(timezone.utc)
            session.exec(delete(AccessToken).where(AccessToken.expires_at < now))
            session.exec(delete(RefreshToken).where(RefreshToken.expires_at < now))
            session.commit()
        print("[TokenCleanupService] Tokens expirados eliminados.")
