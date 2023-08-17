from enum import Enum
from typing import Callable, Type, Annotated
from fastapi import APIRouter, Path, HTTPException, Depends
from fastapi.openapi.docs import get_swagger_ui_html
from razorbill.crud import CRUD
from razorbill.deps import (
    build_exists_dependency,
    build_last_parent_dependency,
    build_pagination_dependency,
    build_path_elements,
    init_deps
)
from typing import Any, Callable, Generic, List, Optional, Type, Union
from ._types import T, DEPENDENCIES
from pydantic import BaseModel, create_model
# GET /project/{project_id}/user/
from razorbill.utils import get_slug_schema_name, schema_factory

def empty_dependency():
    return None

class Router(APIRouter):
    def __init__(
            self,
            crud: CRUD,
            items_per_query: int = 10,
            item_name: str | None = None,
            parent_item_name: str | None = None,
            count_endpoint: bool | list[Callable] = True,
            get_all_endpoint: bool | list[Callable] = True,
            get_one_endpoint: bool | list[Callable] = True,
            create_one_endpoint: bool | list[Callable] = True,
            update_one_endpoint: bool | list[Callable] = True,
            delete_one_endpoint: bool | list[Callable] = True,

            parent_crud: CRUD | None = None,
            path_item_parameter: Type[Path] | None = None,
            prefix: str = '',
            tags: list[str | Enum] | None = None,
            dependencies: list[Depends] | None = None,
            schema_slug: str | None = None,
            **kwargs,
    ):
        self.crud = crud
        #self._parent_id_dependency = Depends(lambda x: x)
        self._parent_id_dependency = Depends(empty_dependency)

        if item_name is None:
            item_name = crud.schema.__name__

        if schema_slug is None:
            self._schema_slug = get_slug_schema_name(item_name)
        fields_to_exclude = ["id", "_id"]
        self.Schema = crud.schema
        self.CreateSchema = crud.create_schema
        self.UpdateSchema = crud.update_schema

        if parent_crud is not None:
            #TODO тут из схемы надо удалить родительйский айди

            if parent_item_name is None:
                parent_item_name = parent_crud.schema.__name__

            # TODO его надо исключить из create and update schemas

            parent_item_tag, _, parent_item_path = build_path_elements(parent_item_name)
            self.CreateSchema = schema_factory(crud.create_schema, parent_item_tag, skip_validation=True)
            self.UpdateSchema = schema_factory(crud.update_schema, parent_item_tag, prefix='Update', skip_validation=True)

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
            tags = [self._schema_slug]

        item_tag, path, item_path = build_path_elements(item_name)
        self._path = path
        self._item_path = item_path
        self._path_field = Path(alias=item_tag) if path_item_parameter is None else path_item_parameter

        self._pagination_dependency = build_pagination_dependency(items_per_query)

        super().__init__(
            dependencies=dependencies,
            prefix=prefix,
            tags=tags,
            **kwargs
        )
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
                status_code=404, detail=f"{self.Schema.__name__} with {self._path_field.alias}={item_id} not found"
            )
    def _init_create_schema_with_project(self):
        class CreateSchemaWithProject(self.CreateSchema):
            project_id: int
        return CreateSchemaWithProject

    def _init_create_one_endpoint(self, deps: list[Callable] | bool):
        @self.post(
            self._path, response_model=self.Schema, dependencies=init_deps(deps)
        )
        async def create_one(
                body: self.CreateSchema,
                parent: dict[str, int] = self._parent_id_dependency,
        ):

            payload = body.dict()
            if parent is not None:
                payload = body.dict() | parent

                # ParentSchema = create_model("DynamicSchema", **parent)
                #
                # class CombinedSchema(self.CreateSchema, ParentSchema):
                #     pass
                #
                # item = await self.crud.create(CombinedSchema(**payload))  # type: ignore
                # return item
            item = await self.crud.create(self.CreateSchema(**payload))  # type: ignore
            print(self.CreateSchema(**payload))
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
                item_id: int = self._path_field,
                body: self.UpdateSchema,
        ):
            payload = body.dict(exclude_unset=True)
            if parent is not None:
                payload = body.dict(exclude_unset=True) | parent

            item = await self.crud.update(item_id, self.UpdateSchema(**payload))  # type: ignore
            if item:
                return item
            raise HTTPException(
                status_code=404, detail=f"{self.Schema.__name__} with {self._path_field.alias}={item_id} not found"
            )

    def _init_delete_one_endpoint(self, deps: list[Callable] | bool):
        @self.delete(self._item_path, dependencies=init_deps(deps))
        async def delete_one(
                parent: dict[str, int] = self._parent_id_dependency,
                item_id: int = self._path_field,
        ):
            if not await self.crud.delete(item_id):
                raise HTTPException(
                    status_code=404, detail=f"{self.Schema.__name__} with {self._path_field.alias}={item_id} not found"
                )

