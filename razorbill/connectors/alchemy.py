import re
from typing import Any, Type
from fastapi import HTTPException
from loguru import logger

from sqlalchemy import and_, func, update, insert
import sqlalchemy
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import class_mapper, joinedload
from sqlalchemy.future import select
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.declarative import DeclarativeMeta

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

        self._schema = self._sqlalchemy_to_pydantic(self.model)
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
            self, obj: dict[str, Any]
    ) -> dict[str, Any]:
        await self.init_model()
        sql_model = self.model(**obj)
        async with self.session_maker.begin() as session:
            session.add(sql_model)
            try:
                await session.commit()
                created_sql_model = await session.merge(sql_model)
                return created_sql_model.__dict__
            except sqlalchemy.exc.IntegrityError as error:
                raise AsyncSQLAlchemyConnectorException(f"Some of relations objects does not exists: {error}")

    async def count(
            self, filters: dict[str, Any] = {}
    ) -> int:
        await self.init_model()
        # TODO тут надо проверить эти filters так как передается None а не {}
        where = []
        if filters is not None:
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
            populate: bool = False,
    ) -> list[dict[str, Any]]:

        await self.init_model()
        statement = select(self.model)

        parent_relationships = []
        if populate:
            for column in self.model.__table__.columns:  # бежим по всем полям модели
                for fk in column.foreign_keys:  # берем только те которые имеют внешний ключ
                    for key, value in filters.items():  # проходимся по фильтрам чтобы вытащить название внешнего ключа
                        if key == column.name:  # если внешний ключ с модели равен ключи с фильтра то проходим
                            for column in self.model.__mapper__.relationships:  # бежим по всем полям с модели которые имеют relationships
                                if fk.column.table == column.entity.class_.__table__:  # если название модели для внешнего ключа == названию модели с relationships
                                    parent_relationships.append(column.key)  # то сохраняем его

        where = []
        if filters:
            where = [getattr(self.model, key) == value for key, value in filters.items()]
        if not parent_relationships:
            statement = statement.where(and_(True, *where)).offset(skip).limit(limit)

            async with self.session_maker.begin() as session:
                result = await session.execute(statement)
                items = result.scalars().all()
        else:
            relationship_attrs = [getattr(self.model, field) for field in parent_relationships]
            statement = statement.where(and_(True, *where)).options(
                *[joinedload(attr) for attr in relationship_attrs]
            ).offset(skip).limit(limit)
            async with self.session_maker.begin() as session:
                result = await session.execute(statement)
                items = result.scalars().all()

        return [self._prepare_result(item, parent_relationships) for item in items]

    async def get_one(
            self,
            obj_id: str | int,
            filters: dict[str, Any] = {},
            populate: bool = False,
    ) -> dict[str, Any] | None:
        await self.init_model()
        statement = select(self.model)
        parent_relationships = []
        if populate:
            if populate:
                for column in self.model.__table__.columns:  # бежим по всем полям модели
                    for fk in column.foreign_keys:  # берем только те которые имеют внешний ключ
                        for key, value in filters.items():  # проходимся по фильтрам чтобы вытащить название внешнего ключа
                            if key == column.name:  # если внешний ключ с модели равен ключи с фильтра то проходим
                                for column in self.model.__mapper__.relationships:  # бежим по всем полям с модели которые имеют relationships
                                    if fk.column.table == column.entity.class_.__table__:  # если название модели для внешнего ключа == названию модели с relationships
                                        parent_relationships.append(column.key)  # то сохраняем его

        statement = statement.where(self.model.id == obj_id)
        if filters:
            where = [getattr(self.model, key) == value for key, value in filters.items()]
            statement = statement.where(and_(True, *where))
        if populate:
            relationship_attrs = [getattr(self.model, field) for field in parent_relationships]
            statement = statement.options(
                *[joinedload(attr) for attr in relationship_attrs]
            )
        async with self.session_maker.begin() as session:
            query = await session.execute(statement)
            try:
                item = query.scalars().one_or_none()
            except NoResultFound:
                item = None

        return self._prepare_result(item, parent_relationships) if item else None

    async def update_one(
            self, obj_id: str | int,
            obj: dict[str, Any],
            filters: dict[str, Any] = {}
    ) -> dict[str, Any]:
        await self.init_model()
        statement = (
            update(self.model)
            .values(obj)
            .where(self.model.id == obj_id)
            .execution_options(synchronize_session="fetch")
        )
        if filters:
            where = [getattr(self.model, key) == value for key, value in filters.items()]
            statement = statement.where(and_(True, *where))

        try:
            async with self.session_maker.begin() as session:
                await session.execute(statement)
                await session.commit()
                updated_obj = await self.get_one(obj_id)

            return updated_obj.__dict__ if updated_obj else None
        except sqlalchemy.exc.IntegrityError as error:
            raise AsyncSQLAlchemyConnectorException(f"Some of relations objects does not exists: {error}")

    async def delete_one(self, obj_id: str | int, filters: dict[str, Any] = {}) -> bool:
        await self.init_model()
        async with self.session_maker.begin() as session:
            statement = select(self.model).where(self.model.id == obj_id)
            where = []
            if filters:
                where = [getattr(self.model, key) == value for key, value in filters.items()]
            statement = statement.where(and_(True, *where))

            query = await session.execute(statement)
            item = query.scalars().one_or_none()

            if item is not None:
                await session.delete(item)
                await session.commit()
                return True
        return False

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

    @staticmethod
    def _pydantic_to_sqlalchemy(pydantic_obj: BaseModel, sqlalchemy_model: DeclarativeMeta) -> DeclarativeBase:
        data = pydantic_obj.dict()
        mapped_fields = {}
        mapper = class_mapper(sqlalchemy_model)

        for field in mapper.columns:
            field_name = field.key
            if field_name in data:
                mapped_fields[field_name] = data[field_name]

        sqlalchemy_instance = sqlalchemy_model(**mapped_fields)
        return sqlalchemy_instance

    @staticmethod
    def _prepare_result(item, parent_relationships):
        if item:
            schema_dict = item.__dict__

            for parent_model_name in parent_relationships:
                parent_data = schema_dict.pop(parent_model_name)
                parent_dict = parent_data.__dict__
                schema_dict[parent_model_name] = parent_dict
            return schema_dict
        return None
