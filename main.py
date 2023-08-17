from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from typing import Type
from pydantic import BaseModel
from razorbill.crud import CRUD
from razorbill.router import Router
from razorbill.connectors.memory import MemoryConnector
from razorbill.connectors.alchemy import AsyncSQLAlchemyConnector
import asyncio

app = FastAPI()

#
# class ProjectSchema(BaseModel):
#     id: int
#     name: str
#
#
# class CreateUserSchema(BaseModel):
#     telegram_id: str
#     telegram_username: str
#     project_id: int
#
#
# class CreateProjectSchema(BaseModel):
#     name: str
#
#
# class UpdateUserSchema(BaseModel):
#     telegram_id: str
#     telegram_username: str
#     project_id: int
#
# from sqlalchemy import Column, Integer, String, ForeignKey
# from sqlalchemy.orm import relationship
# from sqlalchemy.orm import DeclarativeBase
#
#
# class Base(DeclarativeBase):
#     pass
# class User(Base):
#     __tablename__ = 'users'
#
#     id = Column(Integer, primary_key=True)
#     telegram_id = Column(String, nullable=False)
#     telegram_username = Column(String, nullable=False)
#     project_id = Column(Integer, ForeignKey('projects.id'))
#
#     project = relationship("Project", back_populates="users")
#
# class Project(Base):
#     __tablename__ = 'projects'
#
#     id = Column(Integer, primary_key=True)
#     name = Column(String, nullable=False)
#
#     users = relationship("User", back_populates="project")
# # def build_api
#
# #
# # async def test_create(print_flag: bool = True):
# #     @user_crud.before_create
# #     async def before_create_handler(obj: Type[BaseModel]) -> Type[BaseModel]:
# #         if print_flag:
# #             print("user_crud before_create_handler")
# #         if obj.telegram_id == "1":
# #             obj.telegram_id = "2"
# #         return obj
# #
# #     @user_crud.after_create
# #     async def after_create_handler(obj: Type[BaseModel]) -> Type[BaseModel]:
# #         if print_flag:
# #             print("user_crud after_create_handler")
# #         return obj
# #
# #
# #     new_project = CreateProjectSchema(
# #         name="test name"
# #     )
# #
# #     project = await project_crud.create(new_project)
# #     print(project)
# #     new_user_1 = CreateUserSchema(
# #         telegram_id="1",
# #         telegram_username="test1",
# #         project_id=project.id
# #     )
# #     item1 = await user_crud.create(new_user_1)
# #
# #     new_user_2 = CreateUserSchema(
# #         telegram_id="2",
# #         telegram_username="test2",
# #         project_id = project.id
# #     )
# #
# #     item2 = await user_crud.create(new_user_2)
# #     if print_flag:
# #         print("create")
# #         print(item1)
# #         print(item2)
# #
# #
# # async def test_count(print_flag: bool = True):
# #     count_items = await crud.count(filters={"id": 2})
# #     if print_flag:
# #         print("count")
# #         print(count_items)
# #
# #
# # async def test_get_one(print_flag: bool = True):
# #     item = await crud.get_one(obj_id=1)
# #     if print_flag:
# #         print("get_one")
# #         print(item)
# #
# #
# # async def test_get_all(print_flag: bool = True):
# #     items = await crud.get_many(skip=0, limit=5, filters={"telegram_id": '2'})
# #     if print_flag:
# #         print("get_all")
# #         print(items)
# #
# #
# # async def test_update(print_flag: bool = True):
# #     @crud.before_update
# #     async def before_update_handler(obj_id: str | int, obj: Type[BaseModel]) -> Type[BaseModel]:
# #         if print_flag:
# #             print("before_update_handler")
# #             print(obj_id)
# #         if obj.telegram_username == "test3":
# #             obj.telegram_username = "test33"
# #         return obj
# #
# #     @crud.after_update
# #     async def after_update_handler(obj: Type[BaseModel]) -> Type[BaseModel]:
# #         if print_flag:
# #             print("after_update_handler")
# #             print(obj)
# #         return obj
# #
# #     update = UpdateUserSchema(
# #         telegram_id="3",
# #         telegram_username="test3"
# #     )
# #     item = await crud.update(obj_id=1, obj=update)
# #     if print_flag:
# #         print("update")
# #         print(item)
# #
# #
# # async def test_delete(print_flag: bool = True):
# #     @crud.before_delete
# #     async def before_delete_handler(obj_id: str | int) -> str | int:
# #         if print_flag:
# #             print("before_delete_handler")
# #             print(obj_id)
# #         return obj_id
# #
# #     @crud.after_delete
# #     async def after_delete_handler(obj: Type[BaseModel]) -> Type[BaseModel]:
# #         if print_flag:
# #             print("after_delete_handler")
# #             print(obj)
# #         return obj
# #
# #     item = await crud.delete(obj_id=1)
# #     if print_flag:
# #         print("delete")
# #         print(item)
#
#
# async def test_create(print_flag: bool = True):
#
#     # new_user = User(
#     #         telegram_id="5",
#     #         telegram_username="test 5",
#     #         project_id=1
#     #     )
#     # item1 = await user_crud.create(new_user)
#     #print(item1)
#     #®
#     # count = await user_crud.count(filters={"telegram_username": "test 1"})
#     # print(count)
#     #
#     # delete = await user_crud.delete(1)
#
#    # items = await user_crud.get_one(4)
#
#     # new_user = User(
#     #         telegram_id="4",
#     #         telegram_username="test 4"
#     #     )
#     # new_items = await user_crud.update(obj_id=4,obj=new_user)
#     # print(new_items)
#     await user_crud
#     items = await user_crud.get_many(skip=0, limit=10, filters={"project_id": 1})
#     print(items)
#
#


# database_url = 'postgresql+asyncpg://razorbill:secret@localhost:5432/test'
#
# user_connector = AsyncSQLAlchemyConnector(
#     url = database_url,
#     model=User)
#
# user_crud = CRUD(
#     schema=user_connector.schema,
#     connector=user_connector)
#
# asyncio.run(test_create(print_flag=True))

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DeclarativeBase


#
# from razorbill.connectors.alchemy import AsyncSQLAlchemyConnector
# #user_connector = MemoryConnector(UserSchema)
# #

# user_connector = AsyncSQLAlchemyConnector(
#     url=database_url,
#     model=User)
# project_connector = AsyncSQLAlchemyConnector(
#     url=database_url,
#     model=Project)
#
# user_crud = CRUD(
#     connector=user_connector)
# profect_crud = CRUD(
#     connector=project_connector)
#
# router = Router(user_crud, item_name='user')
# app.include_router(router)
#
# project_router = Router(profect_crud, item_name='project')


class UserSchema(BaseModel):
    id: int
    telegram_id: str
    telegram_username: str


class Base(DeclarativeBase):
    pass


from razorbill.builder import builder_router


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, nullable=False)
    telegram_username = Column(String, nullable=False)
    project_id = Column(Integer, ForeignKey('projects.id'))
    project = relationship("Project", back_populates="users")


class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    users = relationship("User", back_populates="project")


database_url = 'postgresql+asyncpg://razorbill:secret@localhost:5432/test'

# user_router = builder_router(alchemy_connector=True, url=database_url, model=User)
# project_router = builder_router(alchemy_connector=True, url=database_url, model=Project)
#
# app.include_router(user_router)
# app.include_router(project_router)
user_connector = AsyncSQLAlchemyConnector(url=database_url,model=User)
user_crud = CRUD(connector= user_connector)

project_connector = AsyncSQLAlchemyConnector(url=database_url,model=Project)
project_crud = CRUD(connector= project_connector)

project_router = Router(project_crud)
user_router = Router(user_crud, parent_crud=project_crud)
app.include_router(project_router)
app.include_router(user_router)





# метод который берет 2 модели педантики и мерджит без валидации динамически
# все ошибки надо обработать
# разобраться почему не правильная схема в свагере
# протестить
# создать одну функцию билдер, который это все собирает
# переключаемся
# добавляем редис


# project_connector = MemoryConnector(ProjectSchema)
# project_crud = CRUD(
#     schema=ProjectSchema,
#     connector=project_connector)

# чтобы распечатать результаты каждого теста, надо передать print_flag = True
# asyncio.run(test_create(print_flag=True))
# asyncio.run(test_count(print_flag=False))
# asyncio.run(test_get_one(print_flag=False))
# asyncio.run(test_get_all(print_flag=False))
# asyncio.run(test_update(print_flag=False))
# asyncio.run(test_delete(print_flag=False))

#
# router = Router(crud=user_crud)
# app.include_router(router)
