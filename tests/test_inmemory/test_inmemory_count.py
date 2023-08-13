import asyncio
import pytest
from crud import  CRUD
from connectors.memory import MemoryConnector, _inmemory_storage
from tests.schemas import UserSchema, ProjectSchema, CreateUserSchema, CreateProjectSchema
from typing import Type
from pydantic import BaseModel




def new_user(telegram_id: str, telegram_username: str, project_id: int = None):
    return CreateUserSchema(
        telegram_id=telegram_id,
        telegram_username=telegram_username,
        project_id=project_id
    )


@pytest.mark.asyncio
async def test_count_without_filter(user_memory_connector):

    user_crud = CRUD(
        schema=UserSchema,
        connector=user_memory_connector)
    count = await user_crud.count()
    assert count == 0
    await user_crud.create(new_user("1", "test1"))
    await user_crud.create(new_user("2", "test2"))
    count = await user_crud.count()
    assert count == 2


@pytest.mark.asyncio
async def test_count_with_filter(user_memory_connector):

    user_crud = CRUD(
        schema=UserSchema,
        connector=user_memory_connector)

    await user_crud.create(new_user("1", "test1"))
    await user_crud.create(new_user("1", "test2"))
    await user_crud.create(new_user("2", "test2"))
    filter = {"telegram_id": "1"}
    count = await user_crud.count(filter)
    assert count == 2
