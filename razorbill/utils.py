import re
from razorbill._types import T
from typing import Any

from typing import Type, TypeVar
from pydantic import BaseModel, create_model, Field

T = TypeVar("T", bound=BaseModel)


def parent_schema_factory(schema_cls: Type[T], pk_field_name: str) -> Type[T]:
    fields = {
        f.name: (f.type_, ...)
        for f in schema_cls.__fields__.values()
    }
    fields[pk_field_name] = (dict[str, Any], Field(None))

    name = schema_cls.__name__
    schema: Type[T] = create_model(__model_name=name, **fields)  # type: ignore
    return schema


def schema_factory(
        schema_cls: Type[T], pk_field_name: str = "_id", prefix: str = "Create", filters: list[str] = None,
        tmp: bool = False
) -> Type[T]:
    if filters is None:
        if prefix == 'Filter':
            fields = {}
        else:
            fields = {
                f.name: (f.type_, ...)
                for f in schema_cls.__fields__.values()
                if f.name != pk_field_name
            }
    else:
        fields = {
            f.name: (f.type_, Field(None))
            for f in schema_cls.__fields__.values()
            if f.name != pk_field_name and f.name in filters
        }

    name = prefix + schema_cls.__name__
    schema: Type[T] = create_model(__model_name=name, **fields)  # type: ignore

    return schema


def get_slug_schema_name(schema_name: str) -> str:
    chunks = re.findall("[A-Z][^A-Z]*", schema_name)
    return "_".join(chunks).lower()


def validate_filters(
        schema_cls: Type[T],
        filters: list[str]
):
    valid_filters = [filter_field for filter_field in filters if filter_field in schema_cls.__annotations__]
    return valid_filters
