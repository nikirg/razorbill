from typing import Any, Type, Callable
from abc import ABC, abstractmethod

from pydantic import BaseModel, validate_arguments
from razorbill.connectors.base import BaseConnector
from razorbill.utils import schema_factory

class CRUD:
    def __init__(
            self,
            connector: Type[BaseConnector] | None = None,
            schema: Type[BaseModel] | None = None,
            create_schema: Type[BaseModel] | None = None,
            update_schema: Type[BaseModel] | None = None,
            overwrite_schema: bool = False,
            overwrite_create_schema: bool = False,
            overwrite_update_schema: bool = False,
            pk: str | None = "id"
    ):
        self.pk: str = pk
        self.schema = schema if schema is not None else connector.schema
        self.create_schema = self.create_schema = (
            create_schema
            if create_schema
            else schema_factory(self.schema, pk_field_name=self.pk, name="Create")
        )
        self.update_schema = (
            update_schema
            if update_schema
            else schema_factory(self.schema, pk_field_name=self.pk, name="Update")
        )
        self.overwrite_schema = overwrite_schema
        self.overwrite_create_schema = overwrite_create_schema
        self.overwrite_update_schema = overwrite_update_schema
        self._connector = connector

        async def dummy(arg: Type[BaseModel] | str | int): return arg

        async def update_dummy(arg_id: str | int, arg: Type[BaseModel] | str | int): return arg

        self._before_create_func = dummy
        self._before_update_func = update_dummy
        self._before_delete_func = dummy

        self._after_create_func = dummy
        self._after_update_func = dummy
        self._after_delete_func = dummy

    
    @validate_arguments
    def before_create(self, func: Callable) -> Callable:
        self._before_create_func = func
        return func

    
    @validate_arguments
    def before_update(self, func: Callable) -> Callable:
        self._before_update_func = func
        return func

    
    @validate_arguments
    def before_delete(self, func: Callable) -> Callable:
        self._before_delete_func = func
        return func

    
    @validate_arguments
    def after_create(self, func: Callable) -> Callable:
        self._after_create_func = func
        return func

    
    @validate_arguments
    def after_update(self, func: Callable) -> Callable:
        self._after_update_func = func
        return func

    
    @validate_arguments
    def after_delete(self, func: Callable) -> Callable:
        self._after_delete_func = func
        return func

    async def count(self, filters: dict[str, Any] = {}) -> int:
        return await self._connector.count(filters=filters)

    async def get_one(self, obj_id: str | int) -> BaseModel:
        return await self._connector.get_one(obj_id=obj_id)

    async def get_many(self, skip: int, limit: int, filters: dict[str, Any] = {},
                       sorting: dict[str, tuple[Any, str]] = {}) -> list[BaseModel]:
        return await self._connector.get_many(skip=skip, limit=limit,
                                              filters=filters)  # TODO, sorting=sorting)

    async def create(self, obj: Type[BaseModel]) -> BaseModel:
        _obj = await self._before_create_func(obj)
        if _obj is None:
            _obj=obj
        record = await self._connector.create_one(obj=_obj)
        record = await self._after_create_func(record)
        # TODO проверить, не делает ли повторную валидацию fastapi в роутере
        return record

    async def update(self, obj_id: str | int, obj: Type[BaseModel]) -> BaseModel:
        _obj = await self._before_update_func(obj_id, obj)
        if _obj is None:
            _obj = obj
        record = await self._connector.update_one(obj_id=obj_id, obj=_obj)
        return await self._after_update_func(record)

    async def delete(self, obj_id: str | int) -> BaseModel:
        await self._before_delete_func(obj_id)
        record = await self._connector.delete_one(obj_id=obj_id)
        return await self._after_delete_func(record)

#
# if __name__ == "main":
#     data_model = ""
#     connector = ""
#     crud = BaseCRUD(data_model, connector)
#
#     @crud.before_create
#     def before_create_handler(object: BaseModel) -> BaseModel:
#         return crud.Schema(**object.dict(), status="on")
#
#     @crud.after_create
#     def after_create_handler(item_id: int | str, object: dict[str, Any]) -> dict[str, Any]:
#         return {}
#
#     @crud.before_update
#     def before_update_handler(item_id: int | str, object: BaseModel) -> BaseModel:
#         return crud.Schema(**object.dict(), updated=True)
#
#     @crud.after_update
#     def after_update_handler(item_id: int | str, object: dict[str, Any]) -> dict[str, Any]:
#         return {}
#
#     @crud.before_delete
#     def before_delete_handler(item_id: int | str):
#         project = crud.get_one(item_id)
#
#         for user_id in project.users:
#             pass
#
#     @crud.after_delete
#     def after_delete_handler(item_id: int | str):
#         pass
#
