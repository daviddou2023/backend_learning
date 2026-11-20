# 目标是：提交 BV 号后写入 SQLite 文件，返回整数 task_id；停止并重启服务后，还能用该 ID 查到 PENDING 任务。
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from enum import Enum
from contextlib import asynccontextmanager


class Base(DeclarativeBase):

    pass

class TaskCreate(BaseModel):
    bvid: str = Field(pattern=r"^BV[0-9A-Za-z]{10}$")

class Status(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class TaskAccepted(BaseModel):
    task_id: int
    status: Status

class GetResponse(BaseModel):
    task_id: int
    bvid: str
    status: Status



class Task(Base):
    __tablename__ = "tasks"
    # 数据库生成任务 ID：主键
    id: Mapped[int] = mapped_column(primary_key=True)
    bvid: Mapped[str] = mapped_column(String(20), nullable=False)
    # 保存用户提交的 BV 号
    # 创建时写入 PENDING
    status: Mapped[str] = mapped_column(String(20), nullable=False)

    
DATABASE_URL = "sqlite+aiosqlite:///./tasks.db"
# engine 管理数据库连接
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(lifespan=lifespan)

# 定义异步依赖
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback() # rollback 撤销当前尚未提交的事务
            raise

@app.post("/tasks", status_code=202, response_model=TaskAccepted)
async def create_task(
    data: TaskCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    task = Task(bvid=data.bvid, status=Status.PENDING.value)
    db.add(task)

    await db.flush()

    task_id = task.id
    await db.commit()

    return {"task_id": task_id, "status": Status.PENDING}

@app.get("/tasks/{task_id}")
async def get_task(
    task_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
    ) -> GetResponse:
    
    task = await db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    get_response = GetResponse(
        task_id=task.id, 
        bvid=task.bvid, 
        status=task.status
    )
    return get_response
