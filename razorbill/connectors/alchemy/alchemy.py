from typing import Any, Type, Container, Optional
from sqlalchemy import and_, func, update, inspect, desc
import sqlalchemy
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import class_mapper, joinedload, DeclarativeBase, sessionmaker
from sqlalchemy.future import select
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from pydantic import BaseModel, create_model
from pydantic import validate_arguments

from razorbill.connectors.base import BaseConnector
from razorbill.connectors.alchemy.utils import _sqlalchemy_to_pydantic, _prepare_result, _get_parent_relationships


class AsyncSQLAlchemyConnectorException(Exception):
    pass


class AsyncSQLAlchemyConnector(BaseConnector):
    @validate_arguments
    def __init__(self, url: str, model: Type[DeclarativeBase], session_maker: Any = None,
                 pk_name: str = "id", **kwargs) -> None:
        self.model = model
        if session_maker is None:
            self.engine = create_async_engine(url, **kwargs)
            self.session_maker = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        else:
            self.session_maker = session_maker
        self._schema = _sqlalchemy_to_pydantic(self.model)
        self._pk_name = pk_name

    @property
    def schema(self) -> Type[BaseModel]:
        return self._schema

    @property
    def pk_name(self) -> str:
        return self._pk_name

    async def create_one(
            self, obj: dict[str, Any]
    ) -> dict[str, Any]:
        sql_model = self.model(**obj)
        async with self.session_maker.begin() as session:
            session.add(sql_model)
            try:
                await session.commit()
                created_sql_model = await session.merge(sql_model)
                return created_sql_model.__dict__
            except sqlalchemy.exc.IntegrityError as error:
                raise AsyncSQLAlchemyConnectorException(f"Some of relations objects does not exists")

    async def count(
            self, filters: dict[str, Any] = {}
    ) -> int:
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
            sorting: dict[str, bool] = None
    ) -> list[dict[str, Any]]:
        statement = select(self.model)

        parent_relationships = []
        where = []
        if filters:
            where = [getattr(self.model, key) == value for key, value in filters.items()]
        if populate:
            parent_relationships = _get_parent_relationships(self.model, filters)
            relationship_attrs = [getattr(self.model, field) for field in parent_relationships]
            statement = statement.options(
                *[joinedload(attr) for attr in relationship_attrs]
            )
            relationship_attrs = [getattr(self.model, field) for field in parent_relationships]
            statement = statement.where(and_(True, *where)).options(
                *[joinedload(attr) for attr in relationship_attrs]
            ).offset(skip).limit(limit)

        else:
            statement = statement.where(and_(True, *where)).offset(skip).limit(limit)

        if sorting:
            for field, sort_desc in sorting.items():
                sort_column = getattr(self.model, field)
                if sort_desc:
                    statement = statement.order_by(desc(sort_column))
                else:
                    statement = statement.order_by(sort_column)

        async with self.session_maker.begin() as session:
            result = await session.execute(statement)
            items = result.scalars().all()

        return [_prepare_result(item, parent_relationships) for item in items]

    async def get_one(
            self,
            obj_id: str | int,
            filters: dict[str, Any] = {},
            populate: bool = False,
    ) -> dict[str, Any] | None:
        statement = select(self.model)
        parent_relationships = []
        statement = statement.where(self.model.id == obj_id)

        if filters:
            where = [getattr(self.model, key) == value for key, value in filters.items()]
            statement = statement.where(and_(True, *where))

        if populate:
            parent_relationships = _get_parent_relationships(self.model, filters)
            relationship_attrs = [getattr(self.model, field) for field in parent_relationships]
            statement = statement.options(
                *[joinedload(attr) for attr in relationship_attrs]
            )
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

        return _prepare_result(item, parent_relationships) if item else None

    async def update_one(
            self, obj_id: str | int,
            obj: dict[str, Any],
            filters: dict[str, Any] = {}
    ) -> dict[str, Any]:
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

            return updated_obj if updated_obj else None
        except sqlalchemy.exc.IntegrityError as error:
            raise AsyncSQLAlchemyConnectorException(f"Some of relations objects does not exists: {error}")

    async def delete_one(self, obj_id: str | int, filters: dict[str, Any] = {}) -> bool:
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
