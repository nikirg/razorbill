from enum import Enum
from typing import Callable, Type

from fastapi import APIRouter, Path, HTTPException, Depends

from razorbill.crud.base import CRUD
from razorbill.converter import build_schema
from razorbill.deps import (
    build_exists_dependency, 
    build_last_parent_dependency, 
    build_pagination_dependency,
    build_path_elements, 
    init_deps
)

# GET /project/{project_id}/user/


class Router(APIRouter):
    def __init__(
        self,
        crud: CRUD,
        # schema: Type[BaseModel] | None = None,
        # create_schema: Type[BaseModel] | None = None,
        # update_schema: Type[BaseModel] | None = None,
        # overwrite_schema: bool = False,
        # overwrite_create_schema: bool = False,
        # overwrite_update_schema: bool = False,
        items_per_query: int = 10,
        count_endpoint: bool | list[Callable] = True,
        get_all_endpoint: bool | list[Callable] = True,
        get_one_endpoint: bool | list[Callable] = True,
        create_one_endpoint: bool | list[Callable] = True,
        update_one_endpoint: bool | list[Callable] = True,
        delete_one_endpoint: bool | list[Callable] = True,
        parent_crud: CRUD | None = None,
        path_item_parameter: Type[Path] | None = None,
        prefix: str | None = None,
        tags: list[str | Enum] | None = None,
        dependencies: list[Depends] | None = None,
        **kwargs,
    ):
        self.crud = crud

        model_name = crud.slug
        fields_to_exclude = ["id", "_id"]
        
        if parent_crud is not None:
            parent_item_tag, _, parent_item_path = build_path_elements(parent_crud.data_model.name)
            parent_exists_dependency = build_exists_dependency(parent_crud, parent_item_tag)
            self._parent_id_dependency = build_last_parent_dependency(parent_item_tag)
            fields_to_exclude.append(parent_item_tag)
            
            if dependencies is not None:
                dependencies.append(parent_exists_dependency)
            else:
                dependencies = [parent_exists_dependency]
            
            if prefix is None:
                prefix = parent_item_path
            else:
                prefix += parent_item_path
            
        if tags is None:
            tags = [model_name.slug]
            
        
        item_tag, path, item_path = build_path_elements(model_name)
        self._path = path
        self._item_path = item_path
        self._path_field = Path(alias=item_tag) if path_item_parameter is None else path_item_parameter

        self._pagination_dependency = build_pagination_dependency(items_per_query)
        
        self.Schema = build_schema(crud.data_model, crud.schema, crud.overwrite_schema, fields_to_exclude)
        self.CreateSchema = build_schema(crud.data_model, crud.create_schema, crud.overwrite_create_schema, fields_to_exclude)
        

        if count_endpoint:
            self._init_count_endpoint(count_endpoint)

        if get_all_endpoint:
            self._init_get_all_endpoint(get_all_endpoint)

        if get_one_endpoint:
            self._init_get_one_endpoint(get_one_endpoint)

        if create_one_endpoint:
            self._init_create_one_endpoint(create_one_endpoint)

        if update_one_endpoint:
            self._init_update_one_endpoint(update_one_endpoint)

        if delete_one_endpoint:
            self._init_delete_one_endpoint(delete_one_endpoint)
            
        super().__init__(
            dependencies=dependencies,
            prefix=prefix,
            tags=tags,
            **kwargs
        )

            
    def _init_count_endpoint(self, deps: list[Callable] | bool):
        @self.get(
            self._path + "count", response_model=int, dependencies=init_deps(deps)
        )
        async def count(
            parent: dict[str, int] = self._parent_id_dependency,
        ) -> int:
            return await self.crud.count(filters=parent)

        
    def _init_get_all_endpoint(self, deps: list[Callable] | bool):
        @self.get(
            self._path,
            response_model=list[self.Schema],
            dependencies=init_deps(deps),
        )
        async def get_many(
            pagination: tuple[str, int] = self._pagination_dependency,
            parent: dict[str, int] = self._parent_id_dependency,
        ):
            skip, limit = pagination
            items = await self.crud.get_many(
                skip=skip, limit=limit, filters=parent
            )
            return items
        
    def _init_get_one_endpoint(self, deps: list[Callable] | bool):
        @self.get(
            self._item_path, response_model=self.Schema, dependencies=init_deps(deps)
        )
        async def get_one(
            item_id: int = self._path_field,
        ):
            item = await self.crud.get_one(item_id)
            if item:
                return item
            raise HTTPException(
                status_code=404, detail=f"item with {item_id=} not found"
            )
        
    def _init_create_one_endpoint(self, deps: list[Callable] | bool):
        @self.post(
            self._path, response_model=self.Schema, dependencies=init_deps(deps)
        )
        async def create_one(
            *,
            parent: dict[str, int] = self._parent_id_dependency,
            body: self.CreateSchema,
        ):
            payload = body.dict() | parent
            item = await self.crud.create_one(payload)

            return item
        
    def _init_update_one_endpoint(self, deps: list[Callable] | bool):
        @self.put(
            self._item_path,
            response_model=self.Schema,
            dependencies=init_deps(deps),
        )
        async def update_one(
            *,
            parent: dict[str, int] = self._parent_id_dependency,
            item_id: int = self.path_field,
            body: self.CreateSchema,
        ):
            payload = body.dict(exclude_unset=True) | parent
            item = await self.crud.update_one(item_id, payload)
            return item
        
    def _init_delete_one_endpoint(self, deps: list[Callable] | bool):
        @self.delete(self._item_path, dependencies=init_deps(deps))
        async def delete_one(
            parent: dict[str, int] = self._parent_id_dependency,
            item_id: int = self._path_field,
        ):
            await self.crud.delete_one(item_id)
    







