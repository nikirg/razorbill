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
async def test_get_many_without_filters(user_memory_connector, project_memory_connector):
    user_crud = CRUD(
        schema=UserSchema,
        connector=user_memory_connector)
    project_crud = CRUD(
        schema=ProjectSchema,
        connector=project_memory_connector)
    project = await project_crud.create(new_project("Test Project"))
    await user_crud.create(new_user("1", "test1", project.id))
    await user_crud.create(new_user("2", "test2", project.id))
    await user_crud.create(new_user("3", "test3"))
    users = await user_crud.get_many(skip=0, limit=10)
    print(f"in get_many without filter {users}")
    assert len(users) == 3


@pytest.mark.asyncio
async def test_get_many_with_filters(user_memory_connector, project_memory_connector):
    user_crud = CRUD(
        schema=UserSchema,
        connector=user_memory_connector)
    project_crud = CRUD(
        schema=ProjectSchema,
        connector=project_memory_connector)
    project = await project_crud.create(new_project("Test Project"))
    await user_crud.create(new_user("1", "test1", project.id))
    await user_crud.create(new_user("2", "test2", project.id))
    await user_crud.create(new_user("3", "test3"))
    filter = {"project_id": project.id}
    users = await user_crud.get_many(skip=0, limit=10, filters=filter)
    print(f"in get_many with filter {users}")
    assert len(users) == 2
