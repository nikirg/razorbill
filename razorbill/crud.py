from typing import Any, Type, Callable, Optional

from razorbill.connectors.base import BaseConnector


class CRUD:
    def __init__(self, connector: Type[BaseConnector]):
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

        self._after_create_func_before_obj = False
        self._after_create_func_parent = False
        self._after_get_many_func_parent = False
        self._after_update_func_before_obj = False

    @property
    def connector(self) -> Type[BaseConnector] | None:
        return self._connector

    def before_create(self, func: Callable) -> Callable:
        self._before_create_func = func
        return func

    def before_update(self, func: Callable) -> Callable:
        self._before_update_func = func
        return func

    def before_delete(self, func: Callable) -> Callable:
        self._before_delete_func = func
        return func

    def before_get_one(self, func: Callable) -> Callable:
        self._before_get_one_func = func
        return func

    def before_get_many(self, func: Callable) -> Callable:
        self._before_get_many_func = func
        return func

    def after_create(self, func: Optional[Callable] = None, *, parent: bool = False, before_obj: bool = False):
        if func is not None:
            self._after_create_func = func
            self._after_create_func_parent = parent
            self._after_create_func_before_obj = before_obj
            return func

        def decorator(f: Callable) -> Callable:
            self._after_create_func = f
            self._after_create_func_parent = parent
            self._after_create_func_before_obj = before_obj
            return f

        return decorator

    def after_update(self, func: Optional[Callable] = None, *, before_obj: bool = False):
        if func is not None:
            self._after_update_func = func
            self._after_update_func_before_obj = before_obj
            return func

        def decorator(f: Callable) -> Callable:
            self._after_update_func = f
            self._after_update_func_before_obj = before_obj
            return f

        return decorator

    def after_delete(self, func: Callable) -> Callable:
        self._after_delete_func = func
        return func

    def after_get_one(self, func: Callable) -> Callable:
        self._after_get_one_func = func
        return func

    def after_get_many(self, func: Optional[Callable] = None, *, parent: bool = False):
        if func is not None:
            self._after_get_many_func = func
            self._after_get_many_func_parent = parent
            return func

        def decorator(f: Callable) -> Callable:
            self._after_get_many_func = f
            self._after_get_many_func_parent = parent
            return f

        return decorator

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        return await self._connector.count(filters=filters)  # type: ignore

    async def get_one(self, obj_id: str | int, populate: list[str] | None = None) -> dict[str, Any]:
        if self._before_get_one_func is not None:
            item = await self._before_get_one_func(obj_id, populate)
            if item is not None: return item

        item = await self._connector.get_one(obj_id=obj_id, populate=populate)  # type: ignore

        if self._after_get_one_func is not None:
            item = await self._after_get_one_func(item)

        return item

    async def get_many(
            self, *,
            skip: int = 0,
            limit: int = 10,
            populate: list[str] | None = None,
            filters: dict[str, Any] | None = None,
            sorting: tuple[str, bool] | None = None,
            parent_obj: Type[dict[str, Any]] | None = None
    ) -> list[dict[str, Any]]:

        if self._before_get_many_func is not None:
            items = await self._before_get_many_func(skip, limit, filters, sorting, populate)
            if items is not None: return items

        record = await self._connector.get_many(
            skip=skip, limit=limit, filters=filters,
            populate=populate, sorting=sorting
        )  # type: ignore

        if self._after_get_many_func is not None:

            if self._after_get_many_func_parent:
                modified_record = await self._after_get_many_func(record, parent_obj)
            else:
                modified_record = await self._after_get_many_func(record)

            if modified_record is not None:
                record = modified_record

        return record

    async def create(self, obj: Type[dict[str, Any]], parent_obj: Type[dict[str, Any]] | None = None) -> dict[str, Any]:
        _obj = None

        if self._before_create_func is not None:
            _obj = await self._before_create_func(obj)

        if _obj is None: _obj = obj

        record = await self._connector.create_one(obj=_obj)  # type: ignore
        if self._after_create_func is not None:
            args = [record]
            if self._after_create_func_parent:
                args.append(parent_obj)

            if self._after_create_func_before_obj:
                args.append(obj)

            modified_record = await self._after_create_func(*args)

            if modified_record is not None:
                record = modified_record

        return record

    async def update(self, obj_id: str | int, obj: Type[dict[str, Any]]) -> dict[str, Any]:
        _obj = None

        if self._before_update_func is not None:
            _obj = await self._before_update_func(obj_id, obj)

        if _obj is None: _obj = obj

        record = await self._connector.update_one(obj_id=obj_id, obj=_obj)  # type: ignore

        if self._after_update_func is not None:
            if self._after_update_func_before_obj:
                modified_record = await self._after_update_func(record, obj)
            else:
                modified_record = await self._after_update_func(record)

            if modified_record is not None:
                record = modified_record

        return record

    async def delete(self, obj_id: str | int):
        if self._before_delete_func is not None:
            await self._before_delete_func(obj_id)

        record = await self._connector.delete_one(obj_id=obj_id)  # type: ignore

        if self._after_delete_func is not None:
            await self._after_delete_func(record)
