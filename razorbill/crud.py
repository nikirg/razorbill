from typing import Any, Type, Callable
from pydantic import validate_arguments
from razorbill.connectors.base import BaseConnector

class CRUD:
    def __init__(
            self,
            connector: Type[BaseConnector] | None = None,
    ):

        self._connector = connector

        self._before_create_func = None
        self._before_update_func = None
        self._before_delete_func = None
        self._before_get_one_func = None
        self._before_get_many_func = None

        self._after_create_func = None
        self._after_update_func = None
        self._after_delete_func = None
        self._after_get_one_func = None
        self._after_get_many_func = None

    @property
    def connector(self) -> Type[BaseConnector]:
        return self._connector

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
    def before_get_one(self, func: Callable) -> Callable:
        self._before_get_one_func = func
        return func

    @validate_arguments
    def before_get_many(self, func: Callable) -> Callable:
        self._before_get_many_func = func
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

    @validate_arguments
    def after_get_one(self, func: Callable) -> Callable:
        self._after_get_one_func = func
        return func

    @validate_arguments
    def after_get_many(self, func: Callable) -> Callable:
        self._after_get_meny_func = func
        return func

    async def count(self, filters: dict[str, Any] = {}) -> int:
        return await self._connector.count(filters=filters)

    async def get_one(self, obj_id: str | int, filters: dict[str, Any] = {}, populate: bool = False) -> dict[
        str, Any]:
        if self._before_get_one_func is not None:
            await self._before_get_one_func(obj_id, filters, populate)
        item = await self._connector.get_one(obj_id=obj_id, filters=filters, populate=populate)
        if self._after_get_one_func is not None:
            item = await self._after_get_one_func(item)
        return item

    async def get_many(self, skip: int, limit: int, filters: dict[str, Any] = {},
                       populate: bool = False,
                       sorting: dict[str, bool] = {}) -> list[dict[str, Any]]:
        _obj = None
        if self._before_get_many_func is not None:
            await self._before_get_many_func(skip, limit, filters, sorting, populate)

        items = await self._connector.get_many(skip=skip, limit=limit,
                                               filters=filters, populate=populate, sorting=sorting)
        if self._after_get_many_func is not None:
            items = await self._after_get_many_func(items)
        return items

    async def create(self, obj: Type[dict[str, Any]]) -> dict[str, Any]:
        _obj = None
        if self._before_create_func is not None:
            _obj = await self._before_create_func(obj)
        if _obj is None:
            _obj = obj
        record = await self._connector.create_one(obj=_obj)
        if self._after_create_func is not None:
            modified_record = await self._after_create_func(record)
            if modified_record is not None:
                record = modified_record
        # TODO проверить, не делает ли повторную валидацию fastapi в роутере
        return record

    async def update(self, obj_id: str | int, obj: Type[dict[str, Any]], filters: dict[str, Any] = {}) -> dict[
        str, Any]:
        _obj = None
        if self._before_update_func is not None:
            _obj = await self._before_update_func(obj_id, obj)
        if _obj is None:
            _obj = obj
        record = await self._connector.update_one(obj_id=obj_id, obj=_obj, filters=filters)
        if self._after_update_func is not None:
            modified_record = await self._after_update_func(record)
            if modified_record is not None:
                record = modified_record
        return record

    async def delete(self, obj_id: str | int, filters: dict[str, Any] = {}):
        if self._before_delete_func is not None:
            await self._before_delete_func(obj_id, filters)
        record = await self._connector.delete_one(obj_id=obj_id, filters=filters)
        if self._after_delete_func is not None:
            await self._after_delete_func(record)
        return record
