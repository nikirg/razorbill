import asyncio
import pytest
from crud import CRUD
from tests.models import User, Project



def new_user(telegram_id: str, telegram_username: str, project_id: int = None):
    return User(
        telegram_id=telegram_id,
        telegram_username=telegram_username,
        project_id=project_id
    )


@pytest.mark.asyncio
async def test_count_without_filter(user_alchemy_connector):
    await user_alchemy_connector.drop_all_tables()
    user_crud = CRUD(
        schema=user_alchemy_connector.schema,
        connector=user_alchemy_connector)
    count = await user_crud.count()
    assert count == 0
    await user_crud.create(new_user("1", "test1"))
    await user_crud.create(new_user("2", "test2"))
    count = await user_crud.count()
    assert count == 2


@pytest.mark.asyncio
async def test_count_with_filter(user_alchemy_connector):
    await user_alchemy_connector.drop_all_tables()
    user_crud = CRUD(
        schema=user_alchemy_connector.schema,
        connector=user_alchemy_connector)

    await user_crud.create(new_user("1", "test1"))
    await user_crud.create(new_user("1", "test2"))
    await user_crud.create(new_user("2", "test2"))
    filter = {"telegram_id": "1"}
    count = await user_crud.count(filter)
    assert count == 2