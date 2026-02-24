import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from django_apcore.registry import get_registry
from django_apcore.shortcuts import executor_call, get_task_status, submit_task


@require_GET
def hello_view(request):
    name = request.GET.get("name", "World")
    result = executor_call("hello", {"name": name}, request=request)
    return JsonResponse(result)


@csrf_exempt
@require_POST
def add_view(request):
    data = json.loads(request.body)
    result = executor_call("math.add", {"a": data["a"], "b": data["b"]}, request=request)
    return JsonResponse(result)


@csrf_exempt
@require_POST
def multiply_view(request):
    data = json.loads(request.body)
    result = executor_call(
        "math.multiply", {"a": data["a"], "b": data["b"]}, request=request
    )
    return JsonResponse(result)


@csrf_exempt
@require_POST
async def submit_task_view(request):
    data = json.loads(request.body)
    module_id = data.get("module_id", "slow.process")
    inputs = data.get("inputs", {})
    task_id = await submit_task(module_id, inputs)
    return JsonResponse({"task_id": task_id})


@require_GET
def task_status_view(request, task_id):
    info = get_task_status(task_id)
    if info is None:
        return JsonResponse({"error": "Task not found"}, status=404)
    return JsonResponse({"task_id": task_id, "status": info.status})


@require_GET
def list_modules_view(request):
    registry = get_registry()
    return JsonResponse({"module_count": registry.count})
