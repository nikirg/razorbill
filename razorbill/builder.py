from typing import Any, Type, TypeVar

from razorbill.crud import CRUD
from razorbill.router import Router
from razorbill.connectors.base import BaseConnector


class Resource:
    pass


def build(connector: Type[BaseConnector], parent_crud: CRUD|None = None, **router_kwargs):
    crud = CRUD(connector)
    router = Router(crud, parent_crud=parent_crud, **router_kwargs)
    
    res
    
    # resources = {}
    # parent_model_name = None

    # for model, parent_model, kwargs in configs:
    #     model_name = model.__name__

    #     if parent_model is not None:
    #         parent_model_name = parent_model.__name__
    #         parent_resource = resources.get(parent_model_name)

    #         if parent_resource is None:
    #             parent_connector = AsyncSQLAlchemyConnector(str(db_config.DATABASE_URL), parent_model)
    #             parent_crud = CRUD(parent_connector)
    #             parent_router = APIRouter(parent_crud)

    #             resources[parent_model_name] = Box(crud=parent_crud, router=parent_router)

    #     connector = AsyncSQLAlchemyConnector(str(db_config.DATABASE_URL), model)
    #     parent_resource = resources.get(parent_model_name)
    #     if parent_resource is None:
    #         parent_crud = None
    #     else:
    #         parent_crud = parent_resource.crud
    #     crud = CRUD(connector)
    #     router = APIRouter(crud, parent_crud=parent_crud, **kwargs)

    #     resources[model_name] = Box(crud=crud, router=router)

    # return Box(resources)
