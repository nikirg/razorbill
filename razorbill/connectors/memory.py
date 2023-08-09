from typing import Any, Callable, Dict, List, Type, cast, Optional, Union
from razorbill.connectors.base import BaseConnector
from pydantic import BaseModel


class MemoryConnector(BaseConnector):
    def __init__(self, schema: Type[BaseModel]) -> None:
        self._storage: List[Type[BaseModel]] = []
        self._id = 1
        self.schema = schema

    def _get_next_id(self) -> int:
        id_ = self._id
        self._id += 1

        return id_

    async def create_one(self, obj: Type[BaseModel]) -> BaseModel:
        obj_with_id = dict(obj, id=self._get_next_id())
        obj_instance = self.schema.parse_obj(obj_with_id)
        self._storage.append(obj_instance)
        return obj_instance

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        filtered_models = self._storage
        if filters:
            filtered_models = [obj for obj in self._storage if
                               all(getattr(obj, key) == value for key, value in filters.items())]
        return len(filtered_models)

    async def get_one(self, obj_id: str | int) -> BaseModel:
        for obj in self._storage:
            if obj.id == obj_id:  # type: ignore
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

        for obj in self._storage:
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

        for ind, obj_ in enumerate(self._storage):
            if obj_.id == obj_id:  # type: ignore
                self._storage[ind] = self.schema(
                    **obj.dict(), id=obj_.id  # type: ignore
                )
                return self._storage[ind]

        raise ValueError("Not found")

    async def delete_one(self, obj_id: str | int) -> BaseModel:
        for ind, obj in enumerate(self._storage):
            if obj.id == obj_id:  # type: ignore
                del self._storage[ind]
                return obj
        raise ValueError("Not found")
