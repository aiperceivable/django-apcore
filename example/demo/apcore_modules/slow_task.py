import time

from apcore import module


@module(id="slow.process", description="Simulate a long-running task")
def slow_process(seconds: int = 5) -> dict:
    time.sleep(seconds)
    return {"message": f"Completed after {seconds} seconds"}
