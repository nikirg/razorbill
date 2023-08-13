from typing import Container, Optional, Type

from pydantic import BaseConfig, BaseModel, create_model
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.properties import ColumnProperty

#from razorbill.model import BaseDataModel


class OrmConfig(BaseConfig):
    orm_mode = True

#
# def build_schema(data_model: Type[BaseDataModel], schema: Type[BaseModel] | None, overwrite_schema: bool, exclude_fields: list[str]):
#     if schema is None:
#         return sqlalchemy_to_pydantic(data_model, exclude=exclude_fields)
#     elif overwrite_schema:
#         return schema
#     else:
#         return sqlalchemy_to_pydantic(data_model, exclude=exclude_fields, base_pydantic_model=schema)
#


def sqlalchemy_to_pydantic(
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

