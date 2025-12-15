from dataclasses import dataclass


@dataclass(frozen=True)
class GrantTokenResponse:
    access_token: str
    token_type: str
    expires_in: int
    id_token: str
    refresh_token: str
    scope: str
    user_id: str
    client_id: str

    def to_dict(self) -> dict:
        return {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
            "id_token": self.id_token,
            "refresh_token": self.refresh_token,
            "scope": self.scope,
            "user_id": self.user_id,
            "client_id": self.client_id,
        }


@dataclass(frozen=True)
class ClientCredentialsGrantRequest:
    client_id: str
    client_secret: str
    client_secret: str
    scope: str | None = None

    def to_dict(self) -> dict:
        return {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.scope,
        }


@dataclass()
class FormTokenRequest:
    grant_type: str
    code: str | None = None
    redirect_uri: str | None = None
    client_id: str | None = None
    code_verifier: str | None = None
    refresh_token: str | None = None

    def to_dict(self) -> dict:
        return {
            "grant_type": self.grant_type,
            "code": self.code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "code_verifier": self.code_verifier,
            "refresh_token": self.refresh_token,
        }


@dataclass
class InstrospectResponse:
    active: bool
    # sub: str | None = None
    client_id: str | None = None
    # type: str | None = None
