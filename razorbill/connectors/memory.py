from typing import Any, Callable, Dict, List, Type, cast, Optional, Union
from razorbill.connectors.base import BaseConnector
from pydantic import BaseModel


class MemoryConnector(BaseConnector):
    def __init__(self, schema: BaseModel) -> None:
        self._storage: List[Type[BaseModel]] = []
        self._id = 1
        self.schema = schema

    def _to_dict(self, schema: Type[BaseModel]) -> dict:
        return schema.dict()

    def _get_next_id(self) -> int:
        id_ = self._id
        self._id += 1

        return id_

    async def create_one(self, obj: dict[str, Any]) -> dict:
        obj = self.schema(**obj, id = self._get_next_id())
        self._storage.append(obj)
        "Expected type 'Type[BaseModel]' (matched generic type '_T'), got 'BaseModel' instead "
        return self._to_dict(obj)

    async def count(self,  filters: dict[str, Any] | None = None) -> int:
        filtered_models = self._storage
        if filters:
            filtered_models = [obj for obj in self._storage if
                               all(getattr(obj, key) == value for key, value in filters.items())]
        return len(filtered_models)

    async def get_one(self,  obj_id: str | int) -> dict:

        for obj in self._storage:
            if obj.get("id") == obj_id:
                return self._to_dict(obj)

        raise ValueError(f"Object with id {obj_id} not found")

    async def get_many(
            self,

            skip: int,
            limit: int,
            filters: dict[str, Any] | None = None,
            populate: list[str] | None = None,
    ) -> list[BaseModel]:
        if table_name not in self.models:
            return []

        models = self.models[table_name]

        if filters:
            filtered_models = [model for model in models if
                               all(getattr(model, key) == value for key, value in filters.items())]
        else:
            filtered_models = models

        if populate:
            # TODO не помню что такое populate
            pass

        return filtered_models[skip: skip + limit]

    async def update_one(
            self,  obj_id: str | int, obj: dict[str, Any]
    ) -> dict | None:
        if obj_id is None:
            raise ValueError("obj_id must be provided")

        if table_name not in self.models:
            raise ValueError("table does not exist")

        models = self.models[table_name]
        updated_model = None
        for index, model in enumerate(models):
            if model.id == obj_id:
                for field in obj:
                    setattr(model, field, getattr(obj, field))
                updated_model = model
                break

        if updated_model:
            return self._to_dict(updated_model)
        raise ValueError("Not found")

    async def delete_one(self,  obj_id: str | int) -> bool:
        models = self.models[table_name]
        for index, model in enumerate(models):
            if model.id == obj_id:
                del self.models[table_name][index]
                return True

        raise ValueError("Not found")
