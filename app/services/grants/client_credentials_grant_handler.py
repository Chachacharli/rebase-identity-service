from app.domain.grants.grant_types import GrantType
from app.domain.tokens.token_response import (
    ClientCredentialsGrantRequest,
    GrantTokenResponse,
)
from app.exceptions.bussiness_exceptions import (
    ScopesNotAllowedException,
    UnauthorizedClientException,
)
from app.repositories.client_application_repository import ClientApplicationRepository
from app.services.client_application_service import ClientService
from app.services.grants.token_grant_handler import TokenGrantHandler
from app.services.token_service import TokenService


class ClientCredentialsGrantHandler(TokenGrantHandler):
    def handle(self, form_data: ClientCredentialsGrantRequest) -> GrantTokenResponse:
        client_repo = ClientApplicationRepository(self.session)
        client_service = ClientService(client_repo)
        client = client_service.get_client(form_data.client_id)

        if GrantType.CLIENT_CREDENTIALS not in client.grant_types:
            raise UnauthorizedClientException()

        is_valid_secret = client_service.validate_client_secret(
            form_data.client_id, form_data.client_secret
        )

        if not is_valid_secret:
            raise UnauthorizedClientException()

        requested_scopes = form_data.scope.split(" ") if form_data.scope else []

        for scope in requested_scopes:
            if scope not in client.scopes:
                raise ScopesNotAllowedException(
                    status_code=400, detail="invalid_scope or unallowed_scope"
                )

        token_service = TokenService(self.session)
        token_pair = token_service.issue_client_token(
            form_data.client_id, form_data.scope
        )

        return GrantTokenResponse(
            access_token=token_pair.access_token,
            token_type="Bearer",
            expires_in=token_pair.expires_in,
            scope=form_data.scope,
            client_id=form_data.client_id,
            id_token=None,
            refresh_token=None,
            user_id=None,
        )
