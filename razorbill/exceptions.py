from fastapi import HTTPException

class AppError(Exception):
    def __init__(self, message: str, status_code: int):
        self.status_code = status_code
        self.message = message


class NotFoundError(AppError):
    def __init__(self, model_name: str, field_name: str, field_value: int):
        self.status_code = 404
        self.message = f"{model_name} with {field_name}={field_value} not found"
        raise HTTPException(status_code=self.status_code, detail=self.message)