from fastapi import FastAPI, Depends
from pydantic import BaseModel, Field

from enum import Enum

class Status(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

class TaskCreate(BaseModel):
    bvid: str = Field(pattern=r"^BV[0-9A-Za-z]{10}$")

class TaskAccepted(BaseModel):
    task_id: str
    status: Status


class TaskStatus(BaseModel):
    task_id: str
    bvid: str
    status: Status
    result: str | None = None
    error: str | None = None


app = FastAPI()

# 需要一个内存管理器负责创建、查询和更新状态
from uuid import uuid4

# 用字典保存任务状态，创建任务管理类
class TaskManager:
    def __init__(self):
        self.tasks: dict[str, TaskStatus] = {} # [str, TaskStatus]标注键值分别是什么参数类型

    # 创建方法接收BV号，生成唯一ID，建立初始状态为 pending 的任务并存入字典
    def create_task(self, bvid: str) -> TaskStatus:
        task_id = str(uuid4())
        task = TaskStatus(
            task_id=task_id,
            bvid=bvid,
            status="pending",
        )
        self.tasks[task_id] = task
        return task

    # 查询方法接收ID
    def get_task(self, task_id: str) -> TaskStatus | None:
        return self.tasks.get(task_id)

    # 更新方法，更新 task 的 TaskStatus
    def update_task(
            self,
            task_id: str,
            status: Status,
            result: str | None,
            error: str | None,
    ) -> TaskStatus | None:
        task = self.tasks.get(task_id)
        if task is None:
            return None
        task.status = status
        task.result = result
        task.error = error
        return task

# 模块级创建管理器
task_manager = TaskManager()

def get_task_manager() -> TaskManager:
    return task_manager # 不写 return TaskManager() 是因为需要全局共享 task_manager 对象

from typing import Annotated
from fastapi import HTTPException

def process_task(task_id: str, bvid: str, manager: TaskManager) -> None:
    manager.update_task(task_id, Status.RUNNING, None, None)
    try:
        result = f"BV 号 {bvid} 的模拟复盘已完成"
    except Exception as exc:
        manager.update_task(
            task_id,
            Status.FAILED,
            None,
            str(exc),
        ) 
    else:
        manager.update_task(
            task_id,
            Status.SUCCESS,
            result,
            None,
        )

from fastapi import BackgroundTasks
from typing import Callable

# Callable 表示返回值是一个函数（可被调用的对象）
def get_task_processor() -> Callable[..., None]:
    return process_task


@app.get("/tasks/{task_id}", response_model=TaskStatus)
async def search_task(
    task_id: str, 
    manager: Annotated[TaskManager, Depends(get_task_manager)],
    ) -> TaskStatus:
    task = manager.get_task(task_id)
    if task is None:
        raise HTTPException(404, "Not find task")
    return task

@app.post("/tasks", response_model=TaskAccepted, status_code=202)
async def post_task(
    data: TaskCreate,
    background_tasks: BackgroundTasks,
    manager: Annotated[TaskManager, Depends(get_task_manager)],
    processor: Annotated[Callable[..., None], Depends(get_task_processor)],
    ) -> TaskAccepted:
    task = manager.create_task(data.bvid)
    # background_tasks.add_task(后台函数, 传给后台函数的参数...)
    background_tasks.add_task(
        processor,
        task.task_id,
        task.bvid,
        manager,
    )

    return TaskAccepted(
        task_id=task.task_id,
        status=task.status,
    )

