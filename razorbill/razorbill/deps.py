from typing import Callable, Type

from fastapi import HTTPException, Depends, Path, Request
from razorbill.razorbill.crud.base import CRUD


def build_exists_dependency(
    crud: CRUD, item_tag: str
) -> Depends:
    """Зависимость, которая берет id элемента из URL и проверяет есть ли данный элемент в базе"""

    async def dep(
        item_id: int = Path(alias=item_tag),
    ):
        item = await crud.get_one(item_id)
        if item is None:
            raise HTTPException(
                status_code=404, detail=f"{crud.name} with {item_id=} not found"
            )

    return Depends(dep)


def build_last_parent_dependency(item_tag: str) -> Depends:
    """Зависимость, которая передает в endpoint id родителя (если он есть)"""

    async def dep(request: Request):
        item_id = request.path_params.get(item_tag)
        if item_id is None:
            return {}
        return {item_tag: int(item_id)}

    return Depends(dep)


def build_pagination_dependency(max_limit: int | None = None) -> Depends:
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


def init_deps(funcs: list[Callable] | bool) -> list[Depends]:
    if isinstance(funcs, list):
        return [Depends(func) for func in funcs]
    return []


def build_path_elements(name: str) -> tuple[str, str, str]:
    """Создает строковые элементы URL"""
    item_tag = name + "_id"
    item_path_tag = "{" + item_tag + "}"
    path = f"/{name}/"
    item_path = path + item_path_tag

    return item_tag, path, item_path