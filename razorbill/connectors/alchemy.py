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
from pydantic import BaseModel, validate_arguments


from razorbill.connectors.base import BaseConnector
from razorbill.converter import OrmConfig


class AsyncSQLAlchemyConnectorException(Exception):
    pass


class AsyncSQLAlchemyConnector(BaseConnector):
    @validate_arguments
    def __init__(self, url: str, model: Type[DeclarativeBase],  **kwargs) -> None:
        self.model = model
        self.engine = create_async_engine(url, **kwargs)
        self.session_maker = async_sessionmaker(self.engine, expire_on_commit=False)
        self._schema = self.sqlalchemy_to_pydantic(self.model)


    @property
    def schema(self) -> Type[BaseModel]:
        return self._schema

        
    async def count(
        self, filters: dict[str, Any] = {}
    ) -> int:
        where = [getattr(self.model, key) == value for key, value in filters.items()]

        statement = select(func.count()).select_from(
            select(self.model).where(and_(*where)).subquery()
        )

        with self.session_maker() as session:
            count = await session.scalars(statement)
        return next(count)

    async def get_many(
        self,
        skip: int,
        limit: int,
        filters: dict[str, Any] = {},
        populate: list[Column] | None = None,
    ) -> list[DeclarativeBase]:
        statement = select(self.model)

        if populate is not None:
            for field in populate:
                statement = statement.join(field)

        where = [getattr(self.model, key) == value for key, value in filters.items()]
        statement = statement.where(and_(*where)).offset(skip).limit(limit)
        
        with self.session_maker() as session:
            items = await session.scalars(statement)
        return items.all()

    async def get_one(
        self,
        obj_id: str | int,
        populate: list[Column] | None = None,
    ) -> Type[DeclarativeBase] | None:
        statement = select(self.model)

        if populate is not None:
            for field in populate:
                statement = statement.join(field)

        statement = statement.where(self.model.id == obj_id)
        with self.session_maker() as session:
            item = await session.scalars(statement).first()
        return self.model(item)

    async def create_one(
        self, obj: DeclarativeBase
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
        self, obj_id: str | int, obj: DeclarativeBase
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

    async def delete_one(self, obj_id: str | int):
        with self.session_maker() as session:
            item = await session.get(self.model, obj_id)
            if item is not None:
                await session.delete(item)
                await session.commit()


    @staticmethod
    def sqlalchemy_to_pydantic(
            db_model: Type,
            *,
            config: Type = OrmConfig,
            exclude: Container[str] = [],
            prefix: str | None = None,
            base_pydantic_model: Type[BaseModel] | None = None,
    ) -> Type[BaseModel]:
        model_name = db_model.__name__

        if prefix is not None:
            model_name = prefix + model_name

        mapper = inspect(db_model)
        fields = {}
        for attr in mapper.attrs:
            if isinstance(attr, ColumnProperty):
                if attr.columns:
                    name = attr.key
                    if name in exclude:
                        continue
                    column = attr.columns[0]
                    python_type: Optional[type] = None
                    if hasattr(column.type, "impl"):
                        if hasattr(column.type.impl, "python_type"):
                            python_type = column.type.impl.python_type
                    elif hasattr(column.type, "python_type"):
                        python_type = column.type.python_type
                    assert python_type, f"Could not infer python_type for {column}"
                    default = None
                    if column.default is None and not column.nullable:
                        default = ...
                    fields[name] = (python_type, default)
        pydantic_model = create_model(
            model_name, __base__=base_pydantic_model, __config__=config, **fields
        )
        return pydantic_model