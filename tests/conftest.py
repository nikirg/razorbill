import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
from ..razorbill.connectors.memory import MemoryConnector, _inmemory_storage
from razorbill.connectors.alchemy.alchemy import AsyncSQLAlchemyConnector
from os import environ
import pytest
from .schemas import UserSchema, ProjectSchema
from .models import User, Project



environ["APP_ENV"] = "test"


@pytest.fixture
def user_memory_connector():
    connector = MemoryConnector(UserSchema)
    yield connector
    _inmemory_storage[UserSchema.__name__] = {}

@pytest.fixture
def project_memory_connector():
    connector = MemoryConnector(ProjectSchema)
    yield connector
    _inmemory_storage[ProjectSchema.__name__] = {}



@pytest.fixture
def user_alchemy_connector():
    database_url = 'postgresql+asyncpg://razorbill:secret@localhost:5432/test'
    connector = AsyncSQLAlchemyConnector(
        url=database_url,
        model=User)

    yield connector


@pytest.fixture
def project_alchemy_connector():
    database_url = 'postgresql+asyncpg://razorbill:secret@localhost:5432/test'
    connector = AsyncSQLAlchemyConnector(
        url=database_url,
        model=Project)
    yield connector


@pytest.fixture(autouse=True)
async def cleanup_database():
    database_url = 'postgresql+asyncpg://razorbill:secret@localhost:5432/test'
    connector = AsyncSQLAlchemyConnector(
        url=database_url,
        model=User)
    await connector.drop_all_tables()
    yield connector
    await connector.drop_all_tables()
