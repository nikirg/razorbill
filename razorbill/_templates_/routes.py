from fastapi import APIRouter, Path, HTTPException

from razorbill import pagination_dependency

from ._templates_.config import router_config
from ._templates_.schemes import _Templates_Schema, _Templates_CreateSchema
from ._templates_ import crud
from ._templates_.deps import (
    ROUTER_DEPS,
    GET_ONE_DEPS,
    GET_MANY_DEPS,
    CREATE_ONE_DEPS,
    UPDATE_ONE_REPS,
    DELETE_ONE_DEPS,
    parent_id_dependency,
)


# prefix, dependencies, parent_id_dependency = build_parents_context(
#    parent_db_model_connectors
# )

path_field = Path(alias=router_config.ITEM_TAG)

router = APIRouter(
    prefix=router_config.PREFIX,
    dependencies=ROUTER_DEPS,
    tags=[router_config.MODEL_NAME],
)

"""
@router.get(
    router_config.PATH + "scheme",
    response_model=dict[str, dict],
    dependencies=init_deps(pass) + [parent_id_dependency],
)
async def get_scheme():
    return {"_templates_Schema": _templates_Schema.schema(), "_templates_CreateSchema": _templates_CreateSchema.schema()}



@router.get(
    router_config.PATH + "count", response_model=int, dependencies=init_deps(count_endpoint)
)
async def count(
    db_session: AsyncSession = Depends(db_model_connector.get_session),
    parent: dict[str, int] = parent_id_dependency,
) -> int:
    return await db_model_connector.count(session=db_session, filters=parent)
"""


@router.get(
    router_config.PATH,
    response_model=list[_Templates_Schema],
    dependencies=GET_MANY_DEPS,
)
async def get_many(
    pagination: tuple[str, int] = pagination_dependency,
    parent: dict[str, int] = parent_id_dependency,
):
    skip, limit = pagination
    return await crud.get_many(skip=skip, limit=limit, filters=parent)


@router.get(
    router_config.ITEM_PATH,
    response_model=_Templates_Schema,
    dependencies=GET_ONE_DEPS,
)
async def get_one(
    item_id: int = path_field,
):
    item = await crud.get_one(item_id)
    if item:
        return item
    raise HTTPException(status_code=404, detail=f"Item with {item_id=} not found")


@router.post(
    router_config.PATH,
    response_model=_Templates_Schema,
    dependencies=CREATE_ONE_DEPS,
)
async def create_one(
    *,
    parent: dict[str, int] = parent_id_dependency,
    body: _Templates_CreateSchema,
):
    payload = body.dict() | parent
    return await crud.create_one(payload)


@router.put(
    router_config.ITEM_PATH,
    response_model=_Templates_Schema,
    dependencies=UPDATE_ONE_REPS,
)
async def update_one(
    *,
    parent: dict[str, int] = parent_id_dependency,
    item_id: int = path_field,
    body: _Templates_CreateSchema,
):
    payload = body.dict(exclude_unset=True) | parent
    return await crud.update_one(item_id, payload)


@router.delete(router_config.ITEM_PATH, dependencies=DELETE_ONE_DEPS)
async def delete_one(
    item_id: int = path_field,
):
    await crud.delete_one(item_id)
