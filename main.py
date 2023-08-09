from pydantic import BaseModel, Field
from fastapi import FastAPI
from typing import Any, Type, Callable
from typing import Any
from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo
from datetime import datetime
from razorbill.crud.base import CRUD
from razorbill.router import Router
from razorbill.connectors.memory import MemoryConnector
import asyncio

app = FastAPI()


class UserSchema(BaseModel):
    id: int
    telegram_id: str
    telegram_username: str


class CreateUserSchema(BaseModel):
    telegram_id: str
    telegram_username: str


class UpdateUserSchema(BaseModel):
    telegram_id: str
    telegram_username: str


connector = MemoryConnector(schema=UserSchema)
crud = CRUD(
    schema=UserSchema,
    # pk = "telegram_id",
    overwrite_create_schema=True,
    connector=connector)


# def build_api


async def test_create(print_flag: bool = True):
    @crud.before_create
    async def before_create_handler(obj: Type[BaseModel]) -> Type[BaseModel]:
        if print_flag:
            print("before_create_handler")
        if obj.telegram_id == "1":
            obj.telegram_id = "2"
        return obj

    @crud.after_create
    async def after_create_handler(obj: Type[BaseModel]) -> Type[BaseModel]:
        if print_flag:
            print("after_create_handler")
        return obj

    new_user_1 = CreateUserSchema(
        telegram_id="1",
        telegram_username="test1"
    )
    new_user_2 = CreateUserSchema(
        telegram_id="2",
        telegram_username="test2"
    )
    item1 = await crud.create(new_user_1)
    item2 = await crud.create(new_user_2)
    if print_flag:
        print("create")
        print(item1)
        print(item2)


async def test_count(print_flag: bool = True):
    count_items = await crud.count(filters={"id": 2})
    if print_flag:
        print("count")
        print(count_items)


async def test_get_one(print_flag: bool = True):
    item = await crud.get_one(obj_id=1)
    if print_flag:
        print("get_one")
        print(item)


async def test_get_all(print_flag: bool = True):
    items = await crud.get_many(skip=0, limit=5, filters={"telegram_id": '2'})
    if print_flag:
        print("get_all")
        print(items)


async def test_update(print_flag: bool = True):
    @crud.before_update
    async def before_update_handler(obj_id: str | int, obj: Type[BaseModel]) -> Type[BaseModel]:
        if print_flag:
            print("before_update_handler")
            print(obj_id)
        if obj.telegram_username == "test3":
            obj.telegram_username = "test33"
        return obj

    @crud.after_update
    async def after_update_handler(obj: Type[BaseModel]) -> Type[BaseModel]:
        if print_flag:
            print("after_update_handler")
            print(obj)
        return obj

    update = UpdateUserSchema(
        telegram_id="3",
        telegram_username="test3"
    )
    item = await crud.update(obj_id=1, obj=update)
    if print_flag:
        print("update")
        print(item)


async def test_delete(print_flag: bool = True):
    @crud.before_delete
    async def before_delete_handler(obj_id: str | int) -> str | int:
        if print_flag:
            print("before_delete_handler")
            print(obj_id)
        return obj_id

    @crud.after_delete
    async def after_delete_handler(obj: Type[BaseModel]) -> Type[BaseModel]:
        if print_flag:
            print("after_delete_handler")
            print(obj)
        return obj

    item = await crud.delete(obj_id=1)
    if print_flag:
        print("delete")
        print(item)


if __name__ == "__main__":
    # чтобы распечатать результаты каждого теста, надо передать print_flag = True
    # asyncio.run(test_create(print_flag=False))
    # asyncio.run(test_count(print_flag=False))
    # asyncio.run(test_get_one(print_flag=False))
    # asyncio.run(test_get_all(print_flag=False))
    # asyncio.run(test_update(print_flag=False))
    # asyncio.run(test_delete(print_flag=False))

    print(f"_storage = {connector._storage}")

    # router = Router(crud=crud)
    # app.include_router(router)
