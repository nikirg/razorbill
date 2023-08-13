import asyncio
import pytest
from crud import CRUD
from tests.models import User
from typing import Type
from pydantic import BaseModel




def new_user(telegram_id: str, telegram_username: str, project_id: int = None):
    return User(
        telegram_id=telegram_id,
        telegram_username=telegram_username,
        project_id=project_id
    )


@pytest.mark.asyncio
async def test_delete(user_alchemy_connector):
    await user_alchemy_connector.drop_all_tables()
    user_crud = CRUD(
        schema=user_alchemy_connector.schema,
        connector=user_alchemy_connector)

    @user_crud.before_delete
    async def before_delete_handler(obj_id: str | int) -> Type[BaseModel]:
        if obj_id == 1:
            obj_id = 2
        return obj_id


    user_1 = await user_crud.create(new_user("1", "test1"))
    user_2 = await user_crud.create(new_user("2", "test2"))
    count = await user_crud.count()
    assert count == 2
    await user_crud.delete(user_1.id)
    count = await user_crud.count()
    assert count == 1




