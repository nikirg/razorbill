import asyncio
import pytest
from ..razorbill.crud import CRUD
from ..razorbill.connectors.memory import MemoryConnector, _inmemory_storage
from .schemas import UserSchema, ProjectSchema, CreateUserSchema, CreateProjectSchema
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
async def test_get_many_without_filters(user_memory_connector):
    user_crud = CRUD(
        schema=UserSchema,
        connector=user_memory_connector)
    await user_crud.create(new_user("1", "test1", 1))
    await user_crud.create(new_user("2", "test2", 1))
    await user_crud.create(new_user("3", "test3"))
    users = await user_crud.get_many(skip=0, limit=10)
    print(f"in get_many without filter {users}")
    assert len(users) == 3


@pytest.mark.asyncio
async def test_get_many_with_filters(user_memory_connector):
    user_crud = CRUD(
        schema=UserSchema,
        connector=user_memory_connector)
    await user_crud.create(new_user("1", "test1", 1))
    await user_crud.create(new_user("2", "test2", 1))
    await user_crud.create(new_user("3", "test3"))
    filter = {"project_id": 1}
    users = await user_crud.get_many(skip=0, limit=10, filters=filter)
    print(f"in get_many with filter {users}")
    assert len(users) == 2
