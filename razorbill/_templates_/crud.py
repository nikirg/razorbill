

from typing import Callable


def get_one():
    pass

def get_many():
    pass

def create_one():
    pass

def update_one():
    pass

def delete_one():
    pass



class Router:
    def register_get_one_callback(self, func: Callable):
        register_callback(func)
            
router = Router()


@router.register_get_one_callback
async def get_one_callback(item):
    return item