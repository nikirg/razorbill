import re
from typing import Any, Type
from fastapi import HTTPException
from loguru import logger

from sqlalchemy import and_, func, update, insert
import sqlalchemy
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.future import select
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql.schema import Column
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, ColumnProperty
from pydantic import BaseModel, validate_arguments
from sqlalchemy import Column, inspect
from sqlalchemy.orm import ColumnProperty
from typing import Type, Container, Optional
from pydantic import BaseModel, create_model
from pydantic.main import BaseConfig as OrmConfig
from sqlalchemy.orm import sessionmaker, scoped_session

from .base import BaseConnector
from ..converter import OrmConfig


class AsyncSQLAlchemyConnectorException(Exception):
    pass


class AsyncSQLAlchemyConnector(BaseConnector):
    @validate_arguments
    def __init__(self, url: str, model: Type[DeclarativeBase], pk_name: str = "id", **kwargs) -> None:
        self.model = model
        self.engine = create_async_engine(url, **kwargs)
        self.session_maker = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        # self.session_maker = AsyncSession(self.engine, expire_on_commit=False)

        self._schema = self.sqlalchemy_to_pydantic(self.model)
        self._pk_name = pk_name

    @property
    def schema(self) -> Type[BaseModel]:
        return self._schema

    @property
    def pk_name(self) -> str:
        return self._pk_name

    # self._pk: str = db_model.__table__.primary_key.columns.keys()[0]
    # self._pk_type: type = _utils.get_pk_type(schema, self._pk)

    async def init_model(self):
        async with self.engine.begin() as connection:
            await connection.run_sync(self.model.metadata.create_all)

    async def drop_all_tables(self):
        async with self.engine.begin() as connection:
            await connection.run_sync(self.model.metadata.drop_all)
            await connection.run_sync(self.model.metadata.create_all)



    async def create_one(
            self, obj: DeclarativeBase
    ) -> Type[BaseModel]:
        await self.init_model()

        async with self.session_maker.begin() as session:
            session.add(obj)
            try:
                await session.commit()
                return self.schema(**obj.__dict__)
            except sqlalchemy.exc.IntegrityError as error:
                raise AsyncSQLAlchemyConnectorException(f"Some of relations objects does not exists: {error}")

    async def count(
            self, filters: dict[str, Any] = {}
    ) -> int:
        await self.init_model()
        where = [getattr(self.model, key) == value for key, value in filters.items()]

        statement = select(func.count()).select_from(
            select(self.model).where(and_(True, *where)).subquery()
        )
        async with self.session_maker.begin() as session:
            count = await session.scalar(statement)
        return count

    async def get_many(
            self,
            skip: int,
            limit: int,
            filters: dict[str, Any] = {},
            populate: list[Column] | None = None,
    ) -> list[BaseModel]:
        await self.init_model()
        statement = select(self.model)

        if populate is not None:
            for field in populate:
                statement = statement.join(field)

        where = [getattr(self.model, key) == value for key, value in filters.items()]
        statement = statement.where(and_(True, *where)).offset(skip).limit(limit)

        async with self.session_maker.begin() as session:
            query = await session.scalars(statement)
            items = query.all()

        schemas = [self.schema(**item.__dict__) for item in items]

        return schemas

    async def get_one(
            self,
            obj_id: str | int,
            populate: list[Column] | None = None,
    ) -> Type[BaseModel] | None:
        await self.init_model()
        statement = select(self.model)

        if populate is not None:
            for field in populate:
                statement = statement.join(field)

        statement = statement.where(self.model.id == obj_id)
        async with self.session_maker.begin() as session:
            query = await session.execute(statement)
            try:
                item = query.scalars().one()
            except NoResultFound:
                item = None
            return self.schema(**item.__dict__) if item else None

    async def update_one(
            self, obj_id: str | int, obj: DeclarativeBase
    ) -> Type[BaseModel]:
        await self.init_model()
        model = type(obj)
        attributes_dict = {
            column.name: getattr(obj, column.name)
            for column in obj.__table__.columns
            if column.name != self.pk_name
        }
        statement = (
            update(model)
            .values(attributes_dict)
            .where(model.id == obj_id)
            .execution_options(synchronize_session="fetch")
        )
        try:
            async with self.session_maker.begin() as session:
                await session.execute(statement)
                await session.commit()
                updated_obj = await self.get_one(obj_id)
            return self.schema(**updated_obj.__dict__) if updated_obj else None
        except sqlalchemy.exc.IntegrityError as error:
            raise AsyncSQLAlchemyConnectorException(f"Some of relations objects does not exists: {error}")

    async def delete_one(self, obj_id: str | int):
        await self.init_model()
        async with self.session_maker.begin() as session:
            item = await session.get(self.model, obj_id)
            if item is not None:
                await session.delete(item)
                await session.commit()

    @staticmethod
    def _sqlalchemy_to_pydantic(
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
