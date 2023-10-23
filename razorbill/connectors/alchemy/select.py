from typing import Any, Type
from sqlalchemy import select, desc
from sqlalchemy.inspection import inspect

from razorbill.connectors.alchemy._types import AlchemyModel

    
def build_select_statement(
    model: Type[AlchemyModel], 
    skip: int = 0, 
    limit: int = 10,
    filters: dict[str, Any]|None = None,
    populate: list[str]|None = None,
    sort: tuple[str, bool]|None = None
) -> Any:
    #relations = inspect(model).relationships.items()
    # key_to_model = {name: rel.mapper.class_ for name, rel in relations}
    
    statement = select(model)
    
    if filters is not None:
        where = [getattr(model, key) == value for key, value in filters.items()]
        statement = statement.where(*where)

    # if populate is not None:
    #     statement = statement.options(joinedload(User.addresses))
        
    #     for key in populate:
    #         if key.lower() in key_to_model:
    #             model_to_join = key_to_model[key.lower()]
    #             statement = statement.join(model_to_join, isouter=True)

    if sort is not None:
        if None not in sort:
            key, is_desc = sort
            attr = getattr(model, key)
            if is_desc: 
                attr = desc(attr)
            statement = statement.order_by(attr)

    statement = statement.offset(int(skip)).limit(int(limit))
    return statement