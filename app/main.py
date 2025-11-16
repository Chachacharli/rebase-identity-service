import asyncio
from contextlib import asynccontextmanager

# Import information of pyproject.toml
import toml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_pagination import add_pagination

from app.api import api_router
from app.core.db import init_db
from app.core.exceptions_handler import register_exception_handlers
from app.services.token_cleanup_service import TokenCleanupService

pyproject_data = toml.load("pyproject.toml")
__version__ = pyproject_data["tool"]["poetry"]["version"]
__name__ = pyproject_data["tool"]["poetry"]["name"]
__description__ = pyproject_data["tool"]["poetry"]["description"]


cleanup_service = TokenCleanupService(interval_seconds=300)


# -----------------------------
# Lifespan handler
# -----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting app...")
    # Init database for the first time
    # TODO: Falta agregar migraciones con Alembic
    init_db()

    # TODO: Agregar forma de acoplar REDIs/cache en vez de guardar tokens en bd

    # Init cleanup service to remove expired tokens periodically
    asyncio.create_task(cleanup_service.start())

    yield
    # Aquí podrías poner lógica de cierre (shutdown)
    print("Closing app...")


app = FastAPI(
    lifespan=lifespan, title=__name__, version=__version__, description=__description__
)

register_exception_handlers(app)

templates = Jinja2Templates(directory="app/templates")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
add_pagination(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
