from typing import Type, Container, Optional
from sqlalchemy import inspect
from sqlalchemy.orm import ColumnProperty
from pydantic import BaseModel, create_model


def sqlalchemy_to_pydantic(
    db_model: Type,
    *,
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
                    if hasattr(column.type.impl, "python_type"): # type: ignore
                        python_type = column.type.impl.python_type # type: ignore
                elif hasattr(column.type, "python_type"):
                    python_type = column.type.python_type
                    
                assert python_type, f"Could not infer python_type for {column}"
                default = None
                
                if column.default is None and not column.nullable:
                    default = ...
                else:
                    python_type = python_type|None # type: ignore
                    
                fields[name] = (python_type, default)
                
    pydantic_model = create_model(model_name, __base__=base_pydantic_model, **fields)
    
    return pydantic_model