from pydantic import BaseModel
from razorbill.crud import CRUD
from razorbill.router import Router
from razorbill.connectors.memory import MemoryConnector
from razorbill.connectors.alchemy.alchemy import AsyncSQLAlchemyConnector
from razorbill.connectors.mongo.mongo import AsyncMongoConnector
from sqlalchemy.orm import DeclarativeBase
from enum import Enum
from typing import Callable, Type, Any
from fastapi import Path, Depends


def builder_crud(
        url: str | None = None,
        schema: Type[BaseModel] | None = None,
        model: Type[DeclarativeBase] | None = None,
        memory_connector: bool | None = True,
        mongo_connector:bool | None = True,
        alchemy_connector: bool | None = False,
        pk: str | None = "id",
        session_maker: Any | None = None
):
    if alchemy_connector:
        if not url or not model:
            return None
        connector = AsyncSQLAlchemyConnector(
            model=model,
            url=url,
            pk_name=pk,
            session_maker=session_maker)
    elif mongo_connector:
        if not url or not schema:
            return None
        connector = AsyncMongoConnector(
            model=schema,
            url=url,
            pk_name=pk)

    else:
        if schema is None:
            return None

        connector = MemoryConnector(
            schema=schema,
            pk_name=pk
        )

    return CRUD(connector=connector)


def builder_router(
        url: str | None = None,
        schema: Type[BaseModel] | None = None,
        model: Type[DeclarativeBase] | None = None,
        memory_connector: bool | None = True,
        alchemy_connector: bool | None = False,
        mongo_connector: bool | None = False,
        create_schema: Type[BaseModel] | None = None,
        update_schema: Type[BaseModel] | None = None,
        overwrite_schema: bool = False,
        overwrite_create_schema: bool = False,
        overwrite_update_schema: bool = False,
        pk: str | None = "id",
        items_per_query: int = 10,
        item_name: str | None = None,
        parent_item_name: str | None = None,
        count_endpoint: bool | list[Callable] = True,
        get_all_endpoint: bool | list[Callable] = True,
        get_one_endpoint: bool | list[Callable] = True,
        create_one_endpoint: bool | list[Callable] = True,
        update_one_endpoint: bool | list[Callable] = True,
        delete_one_endpoint: bool | list[Callable] = True,
        path_item_parameter: Type[Path] | None = None,
        prefix: str = '',
        tags: list[str | Enum] | None = None,
        dependencies: list[Depends] | None = None,
        schema_slug: str | None = None,
        parent_schema: Type[BaseModel] | None = None,
        parent_model: Type[DeclarativeBase] | None = None,
        filters: list[str] | None = None,
        session_maker: Any | None = None
):
    crud = builder_crud(
        url=url,
        schema=schema,
        model=model,
        memory_connector=memory_connector,
        alchemy_connector=alchemy_connector,
        mongo_connector=mongo_connector,
        pk=pk,
        session_maker=session_maker,
    )
    parent_crud = builder_crud(
        url=url,
        schema=parent_schema,
        model=parent_model,
        memory_connector=memory_connector,
        alchemy_connector=alchemy_connector,
        pk=parent_item_name,
        session_maker=session_maker,
    )
    router = Router(
        crud,
        items_per_query=items_per_query,
        item_name=item_name,
        parent_item_name=parent_item_name,
        count_endpoint=count_endpoint,
        get_all_endpoint=get_all_endpoint,
        get_one_endpoint=get_one_endpoint,
        create_one_endpoint=create_one_endpoint,
        update_one_endpoint=update_one_endpoint,
        delete_one_endpoint=delete_one_endpoint,
        parent_crud=parent_crud,
        path_item_parameter=path_item_parameter,
        prefix=prefix,
        tags=tags,
        dependencies=dependencies,
        schema_slug=schema_slug,
        create_schema=create_schema,
        update_schema=update_schema,
        overwrite_schema=overwrite_schema,
        overwrite_create_schema=overwrite_create_schema,
        overwrite_update_schema=overwrite_update_schema,
        filters=filters
    )
    return router
