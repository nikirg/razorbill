from typing import Any, Callable, Dict, List, Type, cast, Optional, Union
from .base import BaseConnector
from pydantic import BaseModel

_inmemory_storage: dict[
    str, dict[int, BaseModel]] = {}  # key = schema_name, value = {key = (pk, parent_pk | None), value = value }


class MemoryConnector(BaseConnector):
    def __init__(self, schema: Type[BaseModel], pk_name: str = "_id") -> None:
        self._id = 1
        self._pk_name = pk_name
        self._schema = schema
        _inmemory_storage[schema.__name__] = {}

    @property
    def pk_name(self) -> str:
        return self._pk_name

    @property
    def schema(self) -> Type[BaseModel]:
        return self._schema

    def _get_next_id(self) -> int:
        id_ = self._id
        self._id += 1

        return id_

    async def create_one(self, obj: Type[BaseModel]) -> BaseModel:
        id = self._get_next_id()
        obj_with_id = dict(obj, id=id)
        obj_instance = self.schema.parse_obj(obj_with_id)
        _inmemory_storage[self.schema.__name__][id] = obj_instance
        return obj_instance

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        filtered_models = _inmemory_storage[self._schema.__name__]
        if filters:
            filtered_models = [obj for obj in filtered_models.values() if
                               all(getattr(obj, key) == value for key, value in filters.items())]
        return len(filtered_models)

    async def get_one(self, obj_id: str | int) -> BaseModel:
        obj = _inmemory_storage[self._schema.__name__].get(obj_id)
        if obj is not None:
            return obj

        raise ValueError(f"Object with id {obj_id} not found")

    async def get_many(
            self,
            skip: int,
            limit: int,
            filters: dict[str, Any] | None = None,
            populate: list[str] | None = None,
    ) -> list[BaseModel]:
        result = []

        for obj_id, obj in _inmemory_storage[self._schema.__name__].items():
            matches_filters = all(getattr(obj, key) == value for key, value in filters.items())
            if matches_filters:
                result.append(obj)

        if populate is not None:
            pass

        return result[skip: skip + limit]

    async def update_one(
            self, obj_id: str | int, obj: Type[BaseModel]
    ) -> BaseModel | None:
        if obj_id is None:
            raise ValueError("obj_id must be provided")

        update_obj = _inmemory_storage[self._schema.__name__].get(obj_id)
        if update_obj is not None:
            _inmemory_storage[self._schema.__name__][obj_id] = self.schema(**obj.dict())
            return _inmemory_storage[self._schema.__name__][obj_id]

        raise ValueError("Not found")

    async def delete_one(self, obj_id: str | int):
        obj = _inmemory_storage[self._schema.__name__].get(obj_id)
        if obj is not None:
            del _inmemory_storage[self._schema.__name__][obj_id]
            return
        raise ValueError("Not found")
