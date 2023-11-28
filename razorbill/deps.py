from typing import Type

from pydantic import BaseModel
from fastapi import HTTPException, Depends, Path, Request, Query, params

from razorbill.crud import CRUD
from razorbill.exceptions import NotFoundError


def build_exists_dependency(crud: CRUD, item_tag: str) -> params.Depends:
    """Зависимость, которая берет id элемента из URL и проверяет есть ли данный элемент в базе"""

    async def dep(item_id: int | str = Path(..., alias=item_tag)):
        item = await crud.get_one(item_id)
        if item is None:
            raise NotFoundError(crud.connector.schema.__name__, item_tag, item_id)
        return item
    return Depends(dep)


# TODO нужно ли тут возвращать словарь, надо подумать
def build_last_parent_dependency(item_tag: str, type_pk: Type[str|int]) -> params.Depends:
    """Зависимость, которая передает в endpoint id родителя (если он есть)"""
    
    async def dep(request: Request):
        item_id = request.path_params.get(item_tag)
        if item_id is None:
            return {}
        return {item_tag: type_pk(item_id)}

    return Depends(dep)


def build_parent_populate_dependency() -> params.Depends:
    async def dep(
        populate_parent: bool | str = Query(False),
    ):
        return populate_parent

    return Depends(dep)


def build_sorting_dependency(obj: Type[BaseModel]) -> params.Depends:
    def get_sortable_fields():
        return list(obj.__fields__.keys())

    async def dep(
            sort_field: str = Query(None, description="Field to sort by", enum=get_sortable_fields()),
            sort_desc: bool = Query(None)
    ):
        return sort_field, sort_desc

    return Depends(dep)


def build_pagination_dependency(max_limit: int | None = None) -> params.Depends:
    """Зависимость, которая валидируют пагинационный параметры запроса"""

    def create_query_validation_exception(field: str, msg: str) -> HTTPException:
        return HTTPException(
            422,
            detail={
                "detail": [
                    {"loc": ["query", field], "msg": msg, "type": "type_error.integer"}
                ]
            },
        )

    def pagination(skip: int = 0, limit: int | None = max_limit) -> tuple[int, int | None]:
        if skip < 0:
            raise create_query_validation_exception(
                field="skip",
                msg="skip query parameter must be greater or equal to zero",
            )

        if limit is not None:
            if limit <= 0:
                raise create_query_validation_exception(
                    field="limit", msg="limit query parameter must be greater then zero"
                )

            elif max_limit and max_limit < limit:
                raise create_query_validation_exception(
                    field="limit",
                    msg=f"limit query parameter must be less then {max_limit}",
                )

        return skip, limit

    return Depends(pagination)

