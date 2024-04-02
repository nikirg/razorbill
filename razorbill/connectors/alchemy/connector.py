from typing import Any, Type

from loguru import logger
from pydantic import BaseModel

import sqlalchemy
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_, func, update, delete
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from razorbill.connectors.alchemy.exceptions import AsyncSQLAlchemyConnectorException

from razorbill.connectors.base import BaseConnector
from razorbill.connectors.alchemy.select import build_select_statement
from razorbill.connectors.alchemy._types import AlchemyModel
from razorbill.connectors.alchemy.converter import sqlalchemy_to_pydantic
from razorbill.connectors.alchemy.utils import object_to_dict


class AsyncSQLAlchemyConnector(BaseConnector):
    def __init__(
        self, 
        model: Type[AlchemyModel],
        db_url: str|None = None, 
        session_maker: sessionmaker|None = None,
        pk_name: str = "id",
        **kwargs
    ):
        self.model = model
        self._columns = model.__table__.columns
        self._column_names = [column.name for column in self._columns]
        
        if session_maker is None:
            if db_url is None:
                raise ValueError("At least one of two arguments is required: ('db_url', 'session_maker')")
            
            engine = create_async_engine(db_url, **kwargs)
            self.session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False) # type: ignore
        else:
            self.session_maker = session_maker
            
        self._schema = sqlalchemy_to_pydantic(self.model)
        self._pk_name = pk_name

    @property
    def schema(self) -> Type[BaseModel]:
        return self._schema

    @property
    def pk_name(self) -> str:
        return self._pk_name

    @property
    def type_pk(self) -> Type[int]:
        return int


    async def create_one(self, obj: dict[str, Any]) -> dict[str, Any]:
        sql_model = self.model(**obj)
        
        async with self.session_maker.begin() as session: # type: ignore
            session.add(sql_model)
            
            try:
                created_sql_model = await session.merge(sql_model)
                result = object_to_dict(created_sql_model)
                await session.commit()
                return result
            
            except sqlalchemy.exc.IntegrityError as error:
                raise AsyncSQLAlchemyConnectorException(f"Some of relations objects does not exists: {error}")


    async def count(self, filters: dict[str, Any]|None = None) -> int:
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
        filters: dict[str, Any]|None = None,
        populate: list[str]|None = None,
        sorting: tuple[str, bool]|None = None
    ) -> list[dict[str, Any]]:
        
        statement = build_select_statement(
            self.model, 
            skip=skip, 
            limit=limit, 
            filters=filters, 
            populate=populate, 
            sort=sorting
        )
        
        async with self.session_maker.begin() as session:
            result = await session.execute(statement)
            items = result.scalars().all()
            return [object_to_dict(item) for item in items]

    async def get_one(self, obj_id: int, populate: list[str]|None = None) -> dict[str, Any]|None:
        try:
            filters = {self._pk_name: int(obj_id)}
        except ValueError:
            return None
        
        statement = build_select_statement(
            self.model, 
            limit=1, 
            filters=filters, 
            populate=populate
        )
        
        async with self.session_maker.begin() as session:
            query = await session.execute(statement)
            item = query.scalars().one_or_none()
            return object_to_dict(item) if item else None

    async def update_one(self, obj_id: int, obj: dict[str, Any]) -> dict[str, Any] | None:
        pk_column = getattr(self.model, self._pk_name)
        try:
            obj_id = int(obj_id)
        except ValueError:
            return None

        # TODO сделать через один запрос и проверить что update session работает и variable_values нормально сохраняется
        statement = (
            update(self.model)
            .values(obj)
            .where(self.model.id == obj_id)
            .execution_options(synchronize_session="fetch")
        )
        try:
            async with self.session_maker.begin() as session:
                await session.execute(statement)
                await session.commit()
                updated_obj = await self.get_one(obj_id)

            return updated_obj if updated_obj else None

        except sqlalchemy.exc.IntegrityError as error:
            raise AsyncSQLAlchemyConnectorException(f"Some of relations objects does not exists: {error}")

    # async def update_one(self, obj_id: int, obj: dict[str, Any]) -> dict[str, Any]|None:
    #     pk_column = getattr(self.model, self._pk_name)
    #     # TODO этот запрос надо проверить на работоспособность
    #     statement = (
    #         update(self.model)
    #         .returning(self.model)
    #         .where(self.model.id == int(obj_id))
    #         .values(obj)
    #         .execution_options(synchronize_session="fetch")
    #     )
    #
    #     try:
    #         async with self.session_maker.begin() as session:
    #             result = await session.execute(statement)
    #             await session.commit()
    #             updated_obj = result.first()
    #         return object_to_dict(updated_obj[0]) if updated_obj else None
    #     except sqlalchemy.exc.IntegrityError as error:
    #         raise AsyncSQLAlchemyConnectorException(f"Some of relations objects does not exists: {error}")
    #
    #     except sqlalchemy.exc.IntegrityError as error:
    #         raise AsyncSQLAlchemyConnectorException(f"Some of relations objects does not exists: {error}")

    async def delete_one(self, obj_id: int) -> dict[str, Any]|None:
        pk_column = getattr(self.model, self._pk_name)

        select_statement = select(self.model).where(pk_column == int(obj_id))
        async with self.session_maker.begin() as session:
            result = await session.execute(select_statement)
            obj_to_delete = result.scalar_one_or_none()

        if obj_to_delete:
            delete_statement = delete(self.model).where(pk_column == int(obj_id))
            async with self.session_maker.begin() as session:
                _ = await session.execute(delete_statement)
            return object_to_dict(obj_to_delete)
