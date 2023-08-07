from pydantic import BaseSettings


class RouterConfig(BaseSettings):
    PATH: str = ""
    PREFIX: str = ""
    ITEM_PATH: str = ""
    ITEM_TAG: str = ""
    MODEL_NAME: str = ""

    # special_function: PyObject = 'math.cos'

    class Config:
        env_prefix = "_TEMPLATES__"
        env_file = ".env"
        env_file_encoding = "utf-8"


router_config = RouterConfig()
