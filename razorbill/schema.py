from typing import Type, Any

from pydantic import BaseModel, create_model, model_validator


def rebuild_schema(
    schema: Type[BaseModel], 
    base_schema: Type[BaseModel]|None = None,
    fields_to_exclude: list[str]|None = None,
    fields_to_include: list[str]|None = None,
    schema_name_prefix: str = ""
) -> Type[BaseModel]:
    
    if fields_to_exclude is None:
        fields_to_exclude = []

    if fields_to_include is None:
        fields_to_include = list(schema.model_fields)
        
    #raise ValueError("Only one of ['fields_to_exclude', 'fields_to_include'] is allowed")

    fields = {}

    for name, info in schema.model_fields.items():
        if name not in fields_to_exclude:
            fields[name] = (info.annotation, ... if info.is_required() else None)
            
    schema_name = schema_name_prefix + schema.__name__
    rebuilded_schema = create_model(schema_name, __base__=base_schema, **fields)
    return rebuilded_schema


if __name__ == "__main__":
    
    class AdditionalCreateSchema(BaseModel):           
        @model_validator(mode="before")
        @classmethod
        def validate_all(cls, data: Any) -> Any:
            print("Валидация", data)
            return data
        
        
    class CreateSchema(BaseModel):
        name: str
     
    class Schema(BaseModel):
        name: str
        core_id: int
        
    NewSchema = rebuild_schema(
        Schema, 
        base_schema=AdditionalCreateSchema, 
        fields_to_exclude=["core_id"]
    )
    
    NewSchema(name="Hello")
    