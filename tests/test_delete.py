import asyncio
import pytest
from ..razorbill.crud import CRUD
from ..razorbill.connectors.memory import MemoryConnector, _inmemory_storage
from .schemas import UserSchema, ProjectSchema, CreateUserSchema, CreateProjectSchema
from typing import Type
from pydantic import BaseModel




def new_user(telegram_id: str, telegram_username: str, project_id: int = None):
    return CreateUserSchema(
        telegram_id=telegram_id,
        telegram_username=telegram_username,
        project_id=project_id
    )


@pytest.mark.asyncio
async def test_delete(user_memory_connector):

    user_crud = CRUD(
        schema=UserSchema,
        connector=user_memory_connector)

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

    print(f"in delete {_inmemory_storage}")



