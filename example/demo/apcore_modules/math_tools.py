from apcore import module


@module(id="math.add", description="Add two numbers")
def add(a: float, b: float) -> dict:
    return {"result": a + b}


@module(id="math.multiply", description="Multiply two numbers")
def multiply(a: float, b: float) -> dict:
    return {"result": a * b}
