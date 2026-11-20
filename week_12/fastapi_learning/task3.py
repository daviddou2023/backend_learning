"""
实现一个三层依赖链：get_token（从 Header 提取）→ get_current_user（验证用户存在）→ require_active_user（检查用户未被冻结）。
创建一个只有登录用户能访问的接口和一个只有管理员能访问的接口。测试时使用 dependency_overrides 替换认证依赖。
"""



from fastapi import FastAPI, Header, HTTPException, Depends
from typing import Annotated
from pydantic import BaseModel

class User(BaseModel):
    id: int
    username: str
    role: str
    is_frozen: bool = False


users_by_token = {
    "demo-token": User(
        id=1,
        username="lisa",
        role="admin",
        is_frozen=False,
    )
}

def verify_token(token: str) -> User | None:
    return users_by_token.get(token)


async def get_token(auth: Annotated[str, Header(alias="Authorization")]) -> str:
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Must be Bearer token")
    return auth[7:]

async def get_current_user(token: Annotated[str, Depends(get_token)]) -> User:
    # Header 的格式：Authorization: Bearer abc123
    user = verify_token(token)
    if not user:
        raise HTTPException(401, "Invalid token")
    return user

async def require_active_user(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.is_frozen:
        raise HTTPException(403, "User is frozen")
    return user

async def require_admin(user: Annotated[User, Depends(require_active_user)]) -> User:
    if user.role != "admin":
        raise HTTPException(403, "Must be Admin")
    return user

app = FastAPI()



@app.delete("/users/{user_id}")
async def ban_user(user_id: int, user: Annotated[User, Depends(require_admin)]):
    return user_id

@app.get("/users")
async def getinfo(user: Annotated[User, Depends(require_active_user)]):
    return user

async def mock_current_user():
    return User(id=1, username="lisa", role="admin", is_frozen=False)

app.dependency_overrides[get_current_user] = mock_current_user

from fastapi.testclient import TestClient

# client 是TestClient创建的测试客户端，可以直接向FastAPI发请求，不需要启动uvicorn
client = TestClient(app) # app是要被测试的应用


def test_admin_user():
    response = client.delete("/users/2")
    assert response.status_code == 204

app.dependency_overrides.clear()

