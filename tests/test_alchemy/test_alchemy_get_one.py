import asyncio
import pytest
from crud import CRUD
from tests.models import User, Project


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
async def test_get_one_without_create(user_alchemy_connector):
    await user_alchemy_connector.drop_all_tables()
    user_crud = CRUD(
        schema=user_alchemy_connector.schema,
        connector=user_alchemy_connector)
    user = await user_crud.get_one(1)
    assert user == None


@pytest.mark.asyncio
async def test_get_one_with_create(user_alchemy_connector):
    await user_alchemy_connector.drop_all_tables()
    user_crud = CRUD(
        schema=user_alchemy_connector.schema,
        connector=user_alchemy_connector)
    await user_crud.create(new_user("1", "test1"))
    user = await user_crud.get_one(1)
    assert user.id == 1
    assert user.telegram_id == "1"
    assert user.telegram_username == "test1"
    assert user.project_id == None
