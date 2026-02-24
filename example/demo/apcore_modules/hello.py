from apcore import module


@module(id="hello", description="Greet someone by name")
def hello_world(name: str = "World") -> dict:
    return {"message": f"Hello, {name}!"}
