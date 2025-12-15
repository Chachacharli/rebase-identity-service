from app.models.client_application import ClientApplication
from app.repositories.client_application_repository import ClientApplicationRepository
from app.schemas.client_applications import ClientApplicationCreate


class ClientService:
    def __init__(self, repository: ClientApplicationRepository):
        self.repository = repository

    def register_client(self, data: ClientApplicationCreate) -> ClientApplication:
        if self.repository.get_by_client_id(data.client_id):
            raise ValueError("Client ID already exists")
        return self.repository.create(data)

    def get_client(self, client_id: str) -> ClientApplication | None:
        return self.repository.get_by_client_id(client_id)

    def list_clients(self) -> list[ClientApplication]:
        return self.repository.list_all()

    def validate_client_secret(self, client_id: str, client_secret: str) -> bool:
        client = self.get_client(client_id)
        if not client:
            return False
        return client.client_secret == client_secret
