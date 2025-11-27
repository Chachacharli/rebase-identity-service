from datetime import datetime

from sqlmodel import Session, select

from app.domain.tokens.token_response import InstrospectResponse
from app.models.access_token import AccessToken


class AccessTokenRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, token: AccessToken) -> AccessToken:
        """Create access token from AccessToken model"""
        self.session.add(token)
        self.session.commit()
        self.session.refresh(token)
        return token

    def get(self, token: str) -> AccessToken | None:
        """Get access token by token"""
        q = select(AccessToken).where(AccessToken.token == token)
        return self.session.exec(q).one_or_none()

    def revoke_by_refresh(self, refresh_id):
        """Revoke all access tokens associated with a refresh token"""
        q = select(AccessToken).where(AccessToken.refresh_token_id == refresh_id)
        for at in self.session.exec(q).all():
            at.revoked = True
            self.session.add(at)
        self.session.commit()

    def revoke(self, access_token: AccessToken):
        """Revoke access token"""
        access_token.revoked = True
        self.session.add(access_token)
        self.session.commit()

    def introspect(self, token: str) -> InstrospectResponse | None:
        """Verify if access token is valid, if not revoke it and return inactive"""
        at = self.get(token)

        if not at:
            return InstrospectResponse(active=False)
        if at.revoked:
            return InstrospectResponse(active=False, client_id=at.client_id)
        if at.expires_at < datetime.utcnow():
            self.revoke(at)
            return InstrospectResponse(active=False, client_id=at.client_id)
        return InstrospectResponse(
            active=True,
            client_id=at.client_id,
        )
