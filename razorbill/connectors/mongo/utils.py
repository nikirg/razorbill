from typing import Any, Type, Container, Optional
from pydantic.fields import Field, ModelField
from pydantic import BaseModel, create_model, BaseConfig
from beanie import Document
from bson import ObjectId
from bson.errors import InvalidId
from beanie import PydanticObjectId
from pydantic import ValidationError
from beanie.odm.documents import DocType
from beanie.odm.utils.pydantic import get_model_fields


def create_beanie_model(
        pydantic_model: Type[BaseModel],
        db_model_name: str,
        exclude: Container[str] = (),
) -> Type[Document]:
    fields = {
        f.name: (f.type_, ...)
        for f in pydantic_model.__fields__.values()
        if f.name not in exclude}
    beanie_model = create_model(
        db_model_name, __base__=Document, __config__=None, **fields
    )
    return beanie_model


def update_mongo_schema(
        schema_cls: Type[BaseModel],
        pk_field_name: str = "id"
) -> BaseModel:

    fields = {
        f.name: (f.type_, ...)
        for f in schema_cls.__fields__.values()
    }
    fields['id'] = ModelField(
        name='id',
        type_=Optional[str],
        required=False,
        default=None,
        alias='_id',
        class_validators=None,
        model_config=BaseConfig,

    )

    name = schema_cls.__name__
    schema: Type[T] = create_model(__model_name=name, **fields)  # type: ignore
    return schema


def _prepare_result(item, parent_relationships):
    if item:
        schema_dict = item
        for parent_model_name in parent_relationships:
            parent_data = schema_dict.pop(parent_model_name, None)
            if parent_data is not None:
                schema_dict[parent_model_name] = parent_data
        return schema_dict
    return None


def _get_parent_relationships(model_name, filters, collection):
    parent_relationships = []
    for key, value in filters.items():
        # Поиск по внешним ключам или другим полям, связанным с родительской коллекцией
        for parent in collection.find({key: value}):
            for parent_field in parent:
                parent_relationships.append(parent_field)
    return parent_relationships


def validate_id(id_str: str) -> PydanticObjectId:
    try:
        obj_id = ObjectId(id_str)
        pydantic_obj_id = PydanticObjectId(obj_id)
        return pydantic_obj_id
    except (ValueError, ValidationError, InvalidId):
        return None