from fastapi.testclient import TestClient
from week1_2 import app, Status, TaskManager, get_task_manager, get_task_processor

import pytest

@pytest.fixture
def client():
    manager = TaskManager()
    app.dependency_overrides[get_task_manager] = lambda: manager # 右边是没有参数的函数，返回是manager
    try:
        # with 上下文管理器
        with TestClient(app) as test_client:
            yield test_client # 暂停 fixture
    finally:
        app.dependency_overrides.pop(get_task_manager, None) 
        app.dependency_overrides.pop(get_task_processor, None)

# 2. 测试BV校验失败
def test_invalid_bvid_returns_422(client):
    response = client.post("/tasks", json={"bvid": "not-a-bv"})
    # 加入断言测试，把预期行为明确写出来
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == "bvid"

# 3. 测试提交后查询
def test_submit_and_query_task(client):
    app.dependency_overrides[get_task_processor] = lambda: fake_success
    # response 是 TestClient 返回的 HTTP 响应对象
    response = client.post("/tasks", json={"bvid": "BV1xx411C7Md"})

    assert response.status_code == 202
    accepted = response.json()
    assert accepted["status"] == "pending"

    task_id = accepted["task_id"]
    status_response = client.get(f"/tasks/{task_id}")

    assert status_response.status_code == 200
    assert status_response.json()["task_id"] == task_id
    assert status_response.json()["status"] == "success"

# 4. 测试未知任务
def test_unknown_task_returns_404(client):
    response = client.get("/tasks/unknown-id")
    assert response.status_code == 404

# 5. 测试模拟成功和失败
def fake_success(task_id, bvid, manager):
    manager.update_task(task_id, Status.SUCCESS, "模拟结果成功", None)

def fake_failure(task_id, bvid, manager):
    manager.update_task(task_id, Status.FAILED, None, "模拟处理错误")

def test_failed_task(client):
    app.dependency_overrides[get_task_processor] = lambda: fake_failure
    response = client.post("/tasks", json={"bvid": "BV1xx411C7Md"})
    assert response.status_code == 202

    task_id = response.json()["task_id"]

    status_response = client.get(f"/tasks/{task_id}")

    assert status_response.status_code == 200
    assert status_response.json()["status"] == "failed"
    assert status_response.json()["error"] == "模拟处理错误"












