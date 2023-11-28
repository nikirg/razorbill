from enum import Enum
from typing import Callable, Type, Any

from pydantic import BaseModel
from fastapi import APIRouter, Path, Depends, params

from razorbill.crud import CRUD
from razorbill.exceptions import NotFoundError, UndefinedParentItemName, UndefinedSchemaException
from razorbill.schema import rebuild_schema
from razorbill.utils import get_slug_schema_name, build_path_elements
from razorbill.deps import (
    build_exists_dependency,
    build_last_parent_dependency,
    build_pagination_dependency,
    build_parent_populate_dependency,
    build_sorting_dependency,
)

_dummy_dependency = Depends(lambda: None)


# class _DummyFilter(BaseModel): pass
# TODO сделать функционал для RESPONSE модел для create read update,
#  response_create_schema(None), overwrite_response_create_schema(False)
#  responce_update_schema, overwrite_response_update_schema
#  response_get_one_schema
# responce_get_many_schema
# reponse_delete_schema


# TODO написать коннектор для REDIS без родительских штук - асинхронный

class Router(APIRouter):
    def __init__(
            self,
            crud: CRUD,
            items_per_query: int = 10,
            item_name: str | None = None,
            parent_item_name: str | None = None,
            parent_crud: CRUD | None = None,
            parent_prefix: str = '',
            count_endpoint: bool | list[params.Depends] = True,
            get_all_endpoint: bool | list[params.Depends] = True,
            get_one_endpoint: bool | list[params.Depends] = True,
            create_one_endpoint: bool | list[params.Depends] = True,
            update_one_endpoint: bool | list[params.Depends] = True,
            delete_one_endpoint: bool | list[params.Depends] = True,
            path_item_parameter: Callable | None = None,
            prefix: str = '',
            tags: list[str | Enum] | None = None,
            dependencies: list[params.Depends] | None = None,
            schema_slug: str | None = None,
            filters: list[str] | None = None,
            schema: Type[BaseModel] | None = None,
            create_schema: Type[BaseModel] | None = None,
            update_schema: Type[BaseModel] | None = None,
            overwrite_schema: bool = False,
            overwrite_create_schema: bool = False,
            overwrite_update_schema: bool = False,
            exclude_from_create_schema: list[str] | None = None,
            exclude_from_update_schema: list[str] | None = None,
            **kwargs
    ):
        super().__init__(dependencies=dependencies, **kwargs)

        self._crud = crud

        self._parent_crud = parent_crud
        self._parent_prefix = parent_prefix
        self._parent_item_name = parent_item_name
        self._parent_exists_dependency = _dummy_dependency
        self._parent_id_dependency = _dummy_dependency
        self._parent_populate_dependency = _dummy_dependency
        self._parent_item_tag = None

        self._build_parent()

        self._overwrite_schema = overwrite_schema
        self._overwrite_create_schema = overwrite_create_schema
        self._overwrite_update_schema = overwrite_update_schema
        self._exclude_from_create_schema = [] if exclude_from_create_schema is None else exclude_from_create_schema
        self._exclude_from_update_schema = [] if exclude_from_update_schema is None else exclude_from_update_schema
        self._Schema = schema
        self._CreateSchema = create_schema
        self._UpdateSchema = update_schema

        self._build_schemes()

        self._sort_field_dependency = build_sorting_dependency(self._Schema)  # type: ignore

        # self._FilterSchema = _DummyFilter

        # if filters is not None:
        #     filters = validate_filters(self._Schema, filters)  # type: ignore
        #     self._FilterSchema = rebuild_schema(
        #         self._CreateSchema,  # type: ignore
        #         fields_to_include=filters,
        #         schema_name_prefix="Filter"
        #     )

        if item_name is None:
            item_name = self._Schema.__name__  # type: ignore

        if schema_slug is None:
            schema_slug = get_slug_schema_name(item_name)

        if tags is None:
            tags = [schema_slug]

        item_tag, path, item_path = build_path_elements(item_name)
        self._path = path
        self._item_path = item_path
        self._path_field = Path(alias=item_tag) if path_item_parameter is None else path_item_parameter
        self._pagination_dependency = build_pagination_dependency(items_per_query)

        self.prefix = prefix
        self.tags = tags

        if count_endpoint:
            self._init_count_endpoint(count_endpoint)

        if get_all_endpoint:
            self._init_get_all_endpoint(get_all_endpoint)

        if get_one_endpoint:
            self._init_get_one_endpoint(get_one_endpoint)

        if create_one_endpoint:
            self._init_create_one_endpoint(create_one_endpoint)

        if update_one_endpoint:
            self._init_update_one_endpoint(create_one_endpoint)

        if delete_one_endpoint:
            self._init_delete_one_endpoint(delete_one_endpoint)

    @property
    def parent_crud(self) -> CRUD | None:
        return self._parent_crud

    @property
    def Schema(self) -> type[BaseModel] | None:
        return self._Schema  # type: ignore

    @property
    def CreateSchema(self) -> type[BaseModel] | None:
        return self._CreateSchema  # type: ignore

    @property
    def UpdateSchema(self) -> type[BaseModel] | None:
        return self._UpdateSchema  # type: ignore

    def _init_deps(self, deps: list[params.Depends] | bool, parent: bool = False) -> list[params.Depends]:
        _deps = []

        if self._parent_exists_dependency is not None and parent:
            _deps.append(self._parent_exists_dependency)

        if isinstance(deps, list):
            _deps.extend(deps)

        return _deps

    def _build_parent(self):
        if self._parent_crud is None:
            return
        if self._parent_item_name is None:
            if (
                    self._parent_crud.connector is None or
                    self._parent_crud.connector.schema is None
            ):
                raise UndefinedParentItemName

            self._parent_item_name = str(self._parent_crud.connector.schema.__name__)  # type: ignore

        parent_item_tag, _, parent_item_path = build_path_elements(self._parent_item_name)

        self._parent_item_tag = parent_item_tag
        self._parent_exists_dependency = build_exists_dependency(self._parent_crud, parent_item_tag)
        self._parent_id_dependency = build_last_parent_dependency(parent_item_tag,
                                                                  self._crud.connector.type_pk)  # type: ignore
        self._parent_populate_dependency = build_parent_populate_dependency()
        self._parent_prefix += parent_item_path

    def _build_schemes(self):
        fields_to_exclude = []
        fields_to_exclude.append(str(self._parent_item_tag))
        
        if self._crud.connector is not None:
            base_schema = self._crud.connector.schema
            primary_key = self._crud.connector.pk_name
            fields_to_exclude.append(str(primary_key))

        if self._Schema is None:
            if self._crud.connector is None:
                raise UndefinedSchemaException

            self._Schema = base_schema
            
        elif not self._overwrite_schema:
            self._Schema = rebuild_schema(
                base_schema,  # type: ignore
                base_schema=self._Schema, # type: ignore
                fields_to_exclude=fields_to_exclude
            )

        if self._CreateSchema is None:
            self._CreateSchema = rebuild_schema(
                self._Schema,  # type: ignore
                fields_to_exclude=fields_to_exclude + self._exclude_from_create_schema,
                schema_name_prefix="Create"
            )
        elif not self._overwrite_create_schema:
            self._CreateSchema = rebuild_schema(
                self._Schema,  # type: ignore
                base_schema=self._CreateSchema,
                fields_to_exclude=fields_to_exclude + self._exclude_from_create_schema,
                schema_name_prefix="Create"
            )

        if self._UpdateSchema is None:
            self._UpdateSchema = rebuild_schema(
                self._Schema,  # type: ignore
                fields_to_exclude=fields_to_exclude + self._exclude_from_update_schema,
                schema_name_prefix="Update"
            )
        elif not self._overwrite_update_schema:
            self._UpdateSchema = rebuild_schema(
                self._Schema,  # type: ignore
                base_schema=self._UpdateSchema,
                fields_to_exclude=fields_to_exclude + self._exclude_from_update_schema,
                schema_name_prefix="Update"
            )

    def _init_count_endpoint(self, deps: bool | list[params.Depends]):
        path = self._parent_prefix + self._path + "count"

        @self.get(path, dependencies=self._init_deps(deps, parent=True))
        async def count(
                parent: dict[str, int] = self._parent_id_dependency,  # type: ignore
                # filters: self._FilterSchema = Depends(self._FilterSchema), # type: ignore
        ) -> int:
            # payload = filters.model_dump(exclude_none=True)
            # if parent is not None:
            #     payload |= parent

            return await self._crud.count(parent)

    def _init_get_all_endpoint(self, deps: bool | list[params.Depends]):
        path = self._parent_prefix + self._path

        @self.get(path, response_model=list[self._Schema],
                  dependencies=self._init_deps(deps, parent=True))  # type: ignore
        async def get_many(
                pagination: tuple[int, int] = self._pagination_dependency,  # type: ignore
                parent_obj: dict[str, Any] = self._parent_exists_dependency,  # type: ignore
                # populate: list[str]|None = None,
                # filters: self._FilterSchema = Depends(self._FilterSchema), # type: ignore
                sorting: tuple[str, bool] | None = self._sort_field_dependency,  # type: ignore
        ):
            # payload = filters.model_dump(exclude_none=True)
            # if parent is not None:
            #     payload |= parent
            skip, limit = pagination
            parent = {}
            if parent_obj is not None:
                parent = {self._parent_item_tag: self._crud.connector.type_pk(parent_obj['id'])}
            items = await self._crud.get_many(
                skip=skip, limit=limit,
                filters=parent, sorting=sorting,
                parent_obj=parent_obj
            )
            return items

    def _init_create_one_endpoint(self, deps: bool | list[params.Depends]):
        path = self._parent_prefix + self._path

        @self.post(path, response_model=self._Schema, dependencies=self._init_deps(deps, parent=True))
        async def create_one(
                body: self._CreateSchema,
                parent_obj: dict[str, Any] = self._parent_exists_dependency,  # type: ignore
        ):
            payload = body.dict()
            if parent_obj is not None:
                parent = {self._parent_item_tag: self._crud.connector.type_pk(parent_obj['id'])}
                payload = body.dict() | parent
            item = await self._crud.create(payload, parent_obj)
            return item

    def _init_get_one_endpoint(self, deps: bool | list[params.Depends]):
        @self.get(
            self._item_path,
            response_model=self._Schema,
            dependencies=self._init_deps(deps)
        )
        async def get_one(
                item_id: int | str = self._path_field,  # type: ignore
                # populate: list[str]|None = None,
        ):
            item = await self._crud.get_one(item_id)  # , populate=populate)
            if item:
                return item
            raise NotFoundError(self._Schema.__name__, self._path_field.alias, item_id)  # type: ignore

    def _init_update_one_endpoint(self, deps: bool | list[params.Depends]):
        @self.put(
            self._item_path,
            response_model=self._Schema,
            dependencies=self._init_deps(deps)
        )
        async def update_one(
                *,
                item_id: int | str = self._path_field,  # type: ignore
                body: self._UpdateSchema,
        ):
            payload = body.dict(exclude_unset=True)

            item = await self._crud.update(item_id, payload)  # type: ignore
            if item:
                return item
            raise NotFoundError(self._Schema.__name__, self._path_field.alias, item_id)  # type: ignore

    def _init_delete_one_endpoint(self, deps: bool | list[params.Depends]):
        @self.delete(self._item_path, dependencies=self._init_deps(deps))
        async def delete_one(item_id: int | str = self._path_field):  # type: ignore
            _ = await self._crud.delete(item_id)
