import re

from typing import Type
from pydantic import BaseModel


def get_slug_schema_name(schema_name: str) -> str:
    if not re.search("[A-Z]", schema_name):
        return schema_name

    chunks = re.findall("[A-Z][^A-Z]*", schema_name)
    return "_".join(chunks).lower()


def validate_filters(schema_cls: Type[BaseModel], filters: list[str]) -> list[str]:
    valid_filters = [
        filter_field for filter_field 
        in filters if filter_field 
        in schema_cls.__annotations__
    ]
    return valid_filters


def camel_to_snake(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def build_path_elements(name: str) -> tuple[str, str, str]:
    """Создает строковые элементы URL"""
    name = camel_to_snake(name)
    item_tag = name + "_id"
    item_path_tag = "{" + item_tag + "}"
    path = f"/{name}/"
    item_path = path + item_path_tag

    return item_tag, path, item_path
