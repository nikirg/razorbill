import asyncio
import pytest
from crud import CRUD
from tests.models import User, Base
from typing import Type
from pydantic import BaseModel



def update_user(user: Base, telegram_id: str, telegram_username: str, ):
    return User(
        id=user.id,
        telegram_id=telegram_id,
        telegram_username=telegram_username,
        project_id=user.project_id
    )


def new_user(telegram_id: str, telegram_username: str, project_id: int = None):
    return User(
        telegram_id=telegram_id,
        telegram_username=telegram_username,
        project_id=project_id
    )


@pytest.mark.asyncio
async def test_update(user_alchemy_connector):
    await user_alchemy_connector.drop_all_tables()
    user_crud = CRUD(
        schema=user_alchemy_connector.schema,
        connector=user_alchemy_connector)

    @user_crud.before_update
    async def before_update_handler(obj_id: str | int, obj: Type[Base]) -> Type[BaseModel]:
        if obj.telegram_id == "2":
            obj.telegram_id = "3"
        return obj

    @user_crud.after_update
    async def after_update_handler(obj: Type[Base]) -> Type[BaseModel]:
        if obj.telegram_id == "3":
            obj.telegram_id = "4"
        return obj

    user = await user_crud.create(new_user("1", "test1"))
    user_id = user.id

    assert user.id == 1
    assert user.telegram_id == '1'
    assert user.telegram_username == 'test1'

    updated_user = await user_crud.update(user_id, update_user(user, "2", "test2"))

    assert updated_user.id == 1
    assert updated_user.telegram_id == '4'
    assert updated_user.telegram_username == 'test2'
