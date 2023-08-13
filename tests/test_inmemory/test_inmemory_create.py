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
async def test_create(user_memory_connector, project_memory_connector):

    user_crud = CRUD(
        schema=UserSchema,
        connector=user_memory_connector)

    project_crud = CRUD(
        schema=ProjectSchema,
        connector=project_memory_connector)

    @user_crud.before_create
    async def before_create_handler(obj: Type[BaseModel]) -> Type[BaseModel]:
        if obj.telegram_id == "1":
            obj.telegram_id = "3"
        return obj

    project = await project_crud.create(new_project("Test Project"))

    user_1 = await user_crud.create(new_user("1", "test1", project.id))
    user_2 = await user_crud.create(new_user("2", "test2"))
    print(f"in create {_inmemory_storage}")
    assert project.id == 1
    assert user_1.telegram_id == '3'
    assert user_2.project_id == None

