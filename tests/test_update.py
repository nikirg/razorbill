import asyncio
import pytest
from ..razorbill.crud import CRUD
from ..razorbill.connectors.memory import MemoryConnector, _inmemory_storage
from .schemas import UserSchema, ProjectSchema, CreateUserSchema, CreateProjectSchema
from typing import Type
from pydantic import BaseModel


def update_user(user: BaseModel, telegram_id: str, telegram_username: str, ):
    return UserSchema(
        id=user.id,
        telegram_id=telegram_id,
        telegram_username=telegram_username,
        project_id=user.project_id
    )


def new_user(telegram_id: str, telegram_username: str, project_id: int = None):
    return CreateUserSchema(
        telegram_id=telegram_id,
        telegram_username=telegram_username,
        project_id=project_id
    )


@pytest.mark.asyncio
async def test_update(user_memory_connector):
    user_crud = CRUD(
        schema=UserSchema,
        connector=user_memory_connector)

    @user_crud.before_update
    async def before_update_handler(obj_id: str | int, obj: Type[BaseModel]) -> Type[BaseModel]:
        if obj.telegram_id == "2":
            obj.telegram_id = "3"
        return obj

    @user_crud.after_update
    async def after_update_handler(obj: Type[BaseModel]) -> Type[BaseModel]:
        if obj.telegram_id == "3":
            obj.telegram_id = "4"
        return obj

    user = await user_crud.create(new_user("1", "test1"))
    user_id = user.id

    assert user.id == 1
    assert user.telegram_id == '1'
    assert user.telegram_username == 'test1'

    updated_user = await user_crud.update(user_id, update_user(user, "2", "test2"))

    print(f"in update {_inmemory_storage}")
    assert updated_user.id == 1
    assert updated_user.telegram_id == '4'
    assert updated_user.telegram_username == 'test2'
