import re
from razorbill._types import T

from typing import Type, TypeVar
from pydantic import BaseModel, create_model, Field

T = TypeVar("T", bound=BaseModel)

def schema_factory(
        schema_cls: Type[T], pk_field_name: str = "_id", prefix: str = "Create", optional=False
) -> Type[T]:
    fields = {
        f.name: (f.type_, Field(None)) if optional else (f.type_, ...)
        for f in schema_cls.__fields__.values()
        if f.name != pk_field_name
    }

    name = prefix + schema_cls.__name__
    schema: Type[T] = create_model(__model_name=name, **fields)  # type: ignore

    return schema


def get_slug_schema_name(schema_name: str) -> str:
    chunks = re.findall("[A-Z][^A-Z]*", schema_name)
    return "_".join(chunks).lower()

