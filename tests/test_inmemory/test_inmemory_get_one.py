import asyncio
import pytest
from crud import CRUD
from connectors.memory import MemoryConnector, _inmemory_storage
from tests.schemas import UserSchema, ProjectSchema, CreateUserSchema, CreateProjectSchema
from typing import Type
from pydantic import BaseModel


def new_project(name):
    return CreateProjectSchema(
        name=name,
    )

def new_user(telegram_id: str, telegram_username: str, project_id: int = None):
    return CreateUserSchema(
        telegram_id=telegram_id,
        telegram_username=telegram_username,
        project_id=project_id
    )


@pytest.mark.asyncio
async def test_get_one_without_create(user_memory_connector):

    user_crud = CRUD(
        schema=UserSchema,
        connector=user_memory_connector)
    with pytest.raises(ValueError, match="Object with id 1 not found"):
        await user_crud.get_one(1)




@pytest.mark.asyncio
async def test_get_one_with_create(user_memory_connector):

    user_crud = CRUD(
        schema=UserSchema,
        connector=user_memory_connector)
    await user_crud.create(new_user("1", "test1"))
    user = await user_crud.get_one(1)
    print(f"in get_one {_inmemory_storage}")
    assert user.id == 1
    assert user.telegram_id == "1"
    assert user.telegram_username == "test1"
    assert user.project_id == None


