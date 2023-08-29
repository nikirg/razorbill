from typing import Any, Type
from .base import BaseConnector
from pydantic import BaseModel

_inmemory_storage: dict[
    str, dict[int, dict[str, Any]]] = {}  # key = schema_name, value = {key = (pk, parent_pk | None), value = value }


class MemoryConnector(BaseConnector):
    def __init__(self, schema: Type[BaseModel], pk_name: str = "id") -> None:
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

    async def create_one(self, obj: dict[str, Any]) -> dict[str, Any]:
        id = self._get_next_id()
        obj_with_id = {**obj, 'id': id}
        _inmemory_storage[self.schema.__name__][id] = obj_with_id
        return obj_with_id

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        filtered_models = _inmemory_storage.get(self._schema.__name__, {})
        if filters:
            filtered_models = [obj for obj in filtered_models.values() if
                               all(obj.get(key) == value for key, value in filters.items())]
        return len(filtered_models)

    async def get_one(self, obj_id: str | int, filters: dict[str, Any] | None = None, populate: list[str] = None, ) -> \
    dict[str, Any] | None:
        obj = _inmemory_storage[self._schema.__name__].get(obj_id)
        foreign_keys = {}
        if obj is not None:
            if filters:
                matches_filters = all(obj.get(key) == value for key, value in filters.items())
                if not matches_filters:
                    return None

            if populate is not None:
                for field in self._schema.__fields__:
                    for fk in populate:
                        parent_fk = fk.replace('Schema', '').lower() + '_id'
                        parent_relationship = fk.replace('Schema', '').lower()
                        if field == parent_fk:
                            foreign_keys[fk] = {
                                'parent_fk': fk.replace('Schema', '').lower() + '_id',
                                'parent_relationship': parent_relationship
                            }

            for schema_name, parent in foreign_keys.items():
                fk_value = obj.get(parent['parent_fk'])
                parent_obj = _inmemory_storage[schema_name].get(fk_value)
                if parent:
                    del obj[parent['parent_fk']]
                    obj[parent['parent_relationship']] = parent_obj

            return obj
        return None

    async def get_many(
            self,
            skip: int,
            limit: int,
            filters: dict[str, Any] | None = None,
            populate: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        result = []
        foreign_keys = {}

        for obj_id, obj in _inmemory_storage.get(self._schema.__name__, {}).items():
            matches_filters = True

            if filters:
                for key, value in filters.items():
                    if obj.get(key) != value:
                        matches_filters = False
                        break

            if matches_filters:
                if populate is not None:
                    for field in self._schema.__fields__:
                        for fk in populate:
                            parent_fk = fk.replace('Schema','').lower() + '_id'
                            parent_relationship = fk.replace('Schema','').lower()
                            if field == parent_fk:
                                foreign_keys[fk] = {
                                    'parent_fk' :fk.replace('Schema','').lower() + '_id',
                                    'parent_relationship': parent_relationship
                                }

                for schema_name, parent in foreign_keys.items():
                    fk_value = obj.get(parent['parent_fk'])
                    parent_obj = _inmemory_storage[schema_name].get(fk_value)
                    if parent:
                        del obj[parent['parent_fk']]
                        obj[parent['parent_relationship']] = parent_obj
                result.append(obj)


        return result[skip: skip + limit]

    async def update_one(
            self, obj_id: str | int,
            obj: dict[str, Any],
            filters: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        if obj_id is not None:
            update_obj = _inmemory_storage.get(self._schema.__name__, {}).get(obj_id)
            if update_obj is not None:
                if filters:
                    matches_filters = all(update_obj.get(key) == value for key, value in filters.items())
                    if not matches_filters:
                        return None
                _obj = obj.copy()
                updated_fields = {key: value for key, value in _obj.items() if key != "id"}
                if updated_fields:
                    updated_fields["id"] = obj_id
                    _inmemory_storage[self._schema.__name__][obj_id].update(updated_fields)
                    return _inmemory_storage[self._schema.__name__][obj_id]
                else:
                    return update_obj
        return None

    async def delete_one(self, obj_id: str | int, filters: dict[str, Any] | None = None) -> bool:
        obj = _inmemory_storage[self._schema.__name__].get(obj_id)
        if obj is not None:
            if filters:
                matches_filters = all(obj.get(key) == value for key, value in filters.items())
                if not matches_filters:
                    return False
            del _inmemory_storage[self._schema.__name__][obj_id]
            return True
        return False
