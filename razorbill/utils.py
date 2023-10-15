import re
from razorbill._types import T
from typing import Any

from typing import Type, TypeVar
from pydantic import BaseModel, create_model, Field, BaseConfig

T = TypeVar("T", bound=BaseModel)


class OrmConfig(BaseConfig):
    orm_mode = True


def create_schema_from_model_with_overwrite(
    schema_cls: Type[T], 
    overwrite_cls: Type[BaseModel],
    pk_field_name: str = "_id", 
    prefix: str = "Create"
) -> Type[T]:
    fields = {}
    for field_name, field_info in schema_cls.__fields__.items():
        if field_name != pk_field_name:
            for overwrite_field_name, overwrite_field_info in overwrite_cls.__fields__.items():
                if field_name == overwrite_field_name:
                    fields[field_name] = (overwrite_field_info.annotation, ... if overwrite_field_info.is_required() else None)
                    break
            fields[field_name] = (field_info.annotation, ... if field_info.is_required() else None)

    name = prefix + schema_cls.__name__
    schema: Type[T] = create_model(__model_name=name, __base__=overwrite_cls, **fields)  # type: ignore
    return schema


def parent_schema_factory(schema_cls: Type[T], pk_field_name: str) -> Type[T]:
    fields = {
        name: (info.annotation, ... if info.is_required() else None)
        for name, info in schema_cls.__fields__.items()
    }
    fields[pk_field_name] = (dict[str, Any], Field(None))
    name = schema_cls.__name__
    config = getattr(schema_cls, "__config__", None)
    schema: Type[T] = create_model(__model_name=name, **fields, __config__=config)  # type: ignore
    return schema


def schema_factory(
    schema_cls: Type[T], 
    exclude_fields: list[str] = ["_id"], 
    prefix: str = "Create", 
    filters: list[str]|None = None
) -> Type[T]:
    if filters is None:
        if prefix == 'Filter':
            fields = {}
        else:
            fields = {
                name: (info.annotation, ... if info.is_required() else None)
                for name, info in schema_cls.__fields__.items()
                if name not in exclude_fields
            }
    else:
        fields = {
            name: (info.annotation, Field(None))
            for name, info in schema_cls.__fields__.items()
            if name not in exclude_fields and name in filters
        }

    name = prefix + schema_cls.__name__
    schema: Type[T] = create_model(__model_name=name, __base__=None, __config__=OrmConfig, **fields)  # type: ignore
    return schema


def get_slug_schema_name(schema_name: str) -> str:
    chunks = re.findall("[A-Z][^A-Z]*", schema_name)
    return "_".join(chunks).lower()


def validate_filters(
        schema_cls: Type[T],
        filters: list[str]
):
    valid_filters = [
        filter_field for filter_field 
        in filters if filter_field 
        in schema_cls.__annotations__
    ]
    return valid_filters
