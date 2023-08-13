import asyncio
import pytest
from crud import CRUD
from tests.models import Project, User
from typing import Type
from pydantic import BaseModel


def new_project(name):
    return Project(
        name=name,
    )

def new_user(telegram_id: str, telegram_username: str, project_id: int = None):
    return User(
        telegram_id=telegram_id,
        telegram_username=telegram_username,
        project_id=project_id
    )


@pytest.mark.asyncio
async def test_create(user_alchemy_connector, project_alchemy_connector):
    await user_alchemy_connector.drop_all_tables()
    await project_alchemy_connector.drop_all_tables()

    user_crud = CRUD(
        schema=user_alchemy_connector.schema,
        connector=user_alchemy_connector)

    project_crud = CRUD(
        schema=project_alchemy_connector.schema,
        connector=project_alchemy_connector)

    @user_crud.before_create
    async def before_create_handler(obj: Type[BaseModel]) -> Type[BaseModel]:
        if obj.telegram_id == "1":
            obj.telegram_id = "3"
        return obj

    project = await project_crud.create(new_project("Test Project"))

    user_1 = await user_crud.create(new_user("1", "test1", project.id))
    user_2 = await user_crud.create(new_user("2", "test2"))
    assert project.id == 1
    assert user_1.telegram_id == '3'
    assert user_2.project_id == None


