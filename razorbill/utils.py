from typing import Type
from pydantic import create_model

from razorbill.types import T

def schema_factory(
    schema_cls: Type[T], pk_field_name: str = "id", name: str = "Create"
) -> Type[T]:
    fields = {
        f.name: (f.type_, ...)
        for f in schema_cls.__fields__.values()
        if f.name != pk_field_name
    }
    name = name+schema_cls.__name__
    schema: Type[T] = create_model(__model_name=name, **fields)  # type: ignore
    return schema
