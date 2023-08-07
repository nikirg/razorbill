import re
from typing import Any, Type
from fastapi import HTTPException
from loguru import logger

from sqlalchemy import and_, func, update, insert
import sqlalchemy
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql.schema import Column
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .razorbill.model import AlchemyModel
from .razorbill.connectors.base import BaseConnector


class AsyncSQLAlchemyConnectorException(Exception):
    pass


class AsyncSQLAlchemyConnector(BaseConnector):
    def __init__(self, url: str, **kwargs) -> None:
        self.engine = create_async_engine(url, **kwargs)
        self.session_maker = async_sessionmaker(self.engine, expire_on_commit=False)
        
    async def count(
        self, model: Type[AlchemyModel], filters: dict[str, Any] = {}
    ) -> int:
        where = [getattr(model, key) == value for key, value in filters.items()]

        statement = select(func.count()).select_from(
            select(model).where(and_(*where)).subquery()
        )

        with self.session_maker() as session:
            count = await session.scalars(statement)
        return next(count)

    async def get_many(
        self,
        model: Type[AlchemyModel],
        skip: int,
        limit: int,
        filters: dict[str, Any] = {},
        populate: list[Column] | None = None,
    ) -> list[AlchemyModel]:
        statement = select(model)

        if populate is not None:
            for field in populate:
                statement = statement.join(field)

        where = [getattr(model, key) == value for key, value in filters.items()]
        statement = statement.where(and_(*where)).offset(skip).limit(limit)
        
        with self.session_maker() as session:
            items = await session.scalars(statement)
        return items.all()

    async def get_one(
        self,
        model: Type[AlchemyModel],
        obj_id: str | int,
        populate: list[Column] | None = None,
    ) -> AlchemyModel | None:
        statement = select(model)

        if populate is not None:
            for field in populate:
                statement = statement.join(field)

        statement = statement.where(model.id == obj_id)
        with self.session_maker() as session:
            item = await session.scalars(statement).first()
        return model(item)

    async def create_one(
        self, obj: AlchemyModel
    ) -> dict[str, Any]:        
        with self.session_maker() as session:
            session.add(obj)

            try:
                await session.commit()
                await session.refresh(obj)
                return obj
            except sqlalchemy.exc.IntegrityError as error:
                raise AsyncSQLAlchemyConnectorException(f"Some of relations objects does not exists: {error}")

    async def update_one(
        self, obj_id: str | int, obj: AlchemyModel
    ) -> dict[str, Any]:
        model = type(obj)
        statement = (
            update(model)
            .values(obj)
            .where(model.id == obj_id)
            .execution_options(synchronize_session="fetch")
        )
        try:
            with self.session_maker() as session:
                await session.execute(statement)
                await session.commit()
            obj["id"] = obj_id
            item = model(**obj)
            return item
        except sqlalchemy.exc.IntegrityError as error:
            raise AsyncSQLAlchemyConnectorException(f"Some of relations objects does not exists: {error}")

    async def delete_one(self, model: Type[AlchemyModel], obj_id: str | int):
        with self.session_maker() as session:
            item = await session.get(model, obj_id)
            if item is not None:
                await session.delete(item)
                await session.commit()
