import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
from ..razorbill.connectors.memory import MemoryConnector, _inmemory_storage
from os import environ
import pytest
from .schemas import UserSchema, ProjectSchema


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