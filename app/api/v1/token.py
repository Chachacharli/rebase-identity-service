from fastapi import APIRouter, Depends, Form, HTTPException

from app.core.config import settings
from app.core.db import Session, get_session
from app.domain.grants.grant_types import GrantType
from app.domain.tokens.authorization_code_grant_request import (
    AuthorizationCodeGrantRequest,
)
from app.domain.tokens.token_response import ClientCredentialsGrantRequest
from app.services.grants.authorization_code_grant_handler import (
    AuthorizationCodeGrantHandler,
)
from app.services.grants.client_credentials_grant_handler import (
    ClientCredentialsGrantHandler,
)
from app.services.grants.refresh_token_grant_handler import RefreshTokenGrantHandler
from app.services.grants.token_grant_handler import TokenGrantHandler

router = APIRouter()

grant_handlers = {
    GrantType.AUTHORIZATION_CODE: AuthorizationCodeGrantHandler,
    GrantType.REFRESH_TOKEN: RefreshTokenGrantHandler,
    GrantType.CLIENT_CREDENTIALS: ClientCredentialsGrantHandler,
}


@router.post("/token")
def token(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    # auth code / refresh
    code: str = Form(None),
    redirect_uri: str = Form(None),
    code_verifier: str = Form(None),
    refresh_token: str = Form(None),
    # client credentials
    client_secret: str = Form(None),
    scope: str = Form(None),
    session: Session = Depends(get_session),
):
    handler_cls = grant_handlers.get(grant_type)
    if not handler_cls:
        raise HTTPException(status_code=400, detail="unsupported_grant_type")

    handler: TokenGrantHandler = handler_cls(settings, session)

    if grant_type == GrantType.CLIENT_CREDENTIALS:
        form_data = ClientCredentialsGrantRequest(
            client_id=client_id,
            client_secret=client_secret,
            scope=scope,
        )
    else:
        form_data = AuthorizationCodeGrantRequest(
            grant_type=grant_type,
            code=code,
            redirect_uri=redirect_uri,
            client_id=client_id,
            code_verifier=code_verifier,
            refresh_token=refresh_token,
        )

    response = handler.handle(form_data)
    session.commit()
    return response.to_dict()
