from fastapi import FastAPI
from typing import Type
from pydantic import BaseModel
from razorbill.crud import CRUD
from razorbill.router import Router
from razorbill.connectors.memory import MemoryConnector, _inmemory_storage
import asyncio

app = FastAPI()


class UserSchema(BaseModel):
    id: int
    telegram_id: str
    telegram_username: str
    project_id: int


class ProjectSchema(BaseModel):
    id: int
    name: str


class CreateUserSchema(BaseModel):
    telegram_id: str
    telegram_username: str
    project_id: int


class CreateProjectSchema(BaseModel):
    name: str


class UpdateUserSchema(BaseModel):
    telegram_id: str
    telegram_username: str
    project_id: int


# def build_api


async def test_create(print_flag: bool = True):
    @user_crud.before_create
    async def before_create_handler(obj: Type[BaseModel]) -> Type[BaseModel]:
        if print_flag:
            print("user_crud before_create_handler")
        if obj.telegram_id == "1":
            obj.telegram_id = "2"
        return obj

    @user_crud.after_create
    async def after_create_handler(obj: Type[BaseModel]) -> Type[BaseModel]:
        if print_flag:
            print("user_crud after_create_handler")
        return obj


    new_project = CreateProjectSchema(
        name="test name"
    )

    project = await project_crud.create(new_project)
    print(project)
    new_user_1 = CreateUserSchema(
        telegram_id="1",
        telegram_username="test1",
        project_id=project.id
    )
    item1 = await user_crud.create(new_user_1)

    new_user_2 = CreateUserSchema(
        telegram_id="2",
        telegram_username="test2",
        project_id = project.id
    )

    item2 = await user_crud.create(new_user_2)
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
    user_connector = MemoryConnector(UserSchema)
    user_crud = CRUD(
        schema=UserSchema,
        connector=user_connector)

    project_connector = MemoryConnector(ProjectSchema)
    project_crud = CRUD(
        schema=ProjectSchema,
        connector=project_connector)

    # чтобы распечатать результаты каждого теста, надо передать print_flag = True
    asyncio.run(test_create(print_flag=True))
    asyncio.run(test_count(print_flag=False))
    # asyncio.run(test_get_one(print_flag=False))
    # asyncio.run(test_get_all(print_flag=False))
    # asyncio.run(test_update(print_flag=False))
    # asyncio.run(test_delete(print_flag=False))

    print(f"_inmemory_storage = {_inmemory_storage}")

    # router = Router(crud=crud)
    # app.include_router(router)
