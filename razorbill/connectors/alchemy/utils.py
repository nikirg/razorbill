from typing import Any, Type, Container, Optional
from sqlalchemy import inspect
from sqlalchemy.orm import class_mapper, DeclarativeBase, ColumnProperty
from sqlalchemy.ext.declarative import DeclarativeMeta
from pydantic import BaseModel, create_model, BaseConfig


class OrmConfig(BaseConfig):
    orm_mode = True


def _sqlalchemy_to_pydantic(
        db_model: Type,
        *,
        config: Type = OrmConfig,
        exclude: Container[str] = [],
        prefix: str | None = None,
        base_pydantic_model: Type[BaseModel] | None = None,
) -> Type[BaseModel]:
    model_name = db_model.__name__

    if prefix is not None:
        model_name = prefix + model_name

    mapper = inspect(db_model)
    fields = {}
    for attr in mapper.attrs:
        if isinstance(attr, ColumnProperty):
            if attr.columns:
                name = attr.key
                if name in exclude:
                    continue
                column = attr.columns[0]
                python_type: Optional[type] = None
                if hasattr(column.type, "impl"):
                    if hasattr(column.type.impl, "python_type"):
                        python_type = column.type.impl.python_type
                elif hasattr(column.type, "python_type"):
                    python_type = column.type.python_type
                assert python_type, f"Could not infer python_type for {column}"
                default = None
                if column.default is None and not column.nullable:
                    default = ...
                fields[name] = (python_type, default)
    pydantic_model = create_model(
        model_name, __base__=base_pydantic_model, __config__=config, **fields
    )
    return pydantic_model


def _pydantic_to_sqlalchemy(pydantic_obj: BaseModel, sqlalchemy_model: DeclarativeMeta) -> DeclarativeBase:
    data = pydantic_obj.dict()
    mapped_fields = {}
    mapper = class_mapper(sqlalchemy_model)

    for field in mapper.columns:
        field_name = field.key
        if field_name in data:
            mapped_fields[field_name] = data[field_name]

    sqlalchemy_instance = sqlalchemy_model(**mapped_fields)
    return sqlalchemy_instance


def _prepare_result(item, parent_relationships):
    if item:
        schema_dict = item.__dict__

        for parent_model_name in parent_relationships:
            parent_data = schema_dict.pop(parent_model_name)
            parent_dict = parent_data.__dict__
            schema_dict[parent_model_name] = parent_dict
        return schema_dict
    return None


def _get_parent_relationships(model: Type[DeclarativeBase], filters: dict[str, Any]) -> list[str]:
    parent_relationships = []
    for column in model.__table__.columns:
        for fk in column.foreign_keys:
            for key, value in filters.items():
                if key == column.name:
                    for rel in model.__mapper__.relationships:
                        if fk.column.table == rel.entity.class_.__table__:
                            parent_relationships.append(rel.key)
    return parent_relationships
