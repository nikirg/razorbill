from typing import Type
from pydantic import create_model
import re
from razorbill._types import T

from typing import Type, TypeVar
from pydantic import BaseModel, create_model

T = TypeVar("T", bound=BaseModel)


def schema_factory(
        schema_cls: Type[T], pk_field_name: str = "_id", prefix: str = "Create", skip_validation: bool = False
) -> Type[T]:
    fields = {
        f.name: (f.type_, ...)
        for f in schema_cls.__fields__.values()
        if f.name != pk_field_name
    }

    name = prefix + schema_cls.__name__
    schema: Type[T] = create_model(__model_name=name, **fields)  # type: ignore
    if skip_validation:
        def skip_validation_method(cls, value):
            return value

        for field_name in schema.__annotations__:
            setattr(schema, field_name, skip_validation_method)

    return schema


def get_slug_schema_name(schema_name: str) -> str:
    chunks = re.findall("[A-Z][^A-Z]*", schema_name)
    return "_".join(chunks).lower()
