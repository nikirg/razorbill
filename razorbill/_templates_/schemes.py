from pydantic import BaseModel



if __name__ == "__main__":
    obj = _Templates_Schema(hello="hi!")
    
    import inspect
    
    print(
        inspect.getsource(_Templates_Schema)
    )
    