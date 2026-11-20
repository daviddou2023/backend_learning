"""
定义完整的用户注册系统模型：UserCreate（用户名3-20字符、邮箱正则、密码8位以上）和 UserOut（不含密码）。
再定义一个 ProductCreate 模型（名称、价格大于0、库存整数、分类枚举）。尝试传入非法数据，观察 FastAPI 返回的 422 错误详情。
"""

from pydantic import BaseModel, Field
from fastapi import FastAPI
from enum import Enum
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=20)
    email: str = Field(pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    password: str = Field(min_length=8)

class UserOut(BaseModel):
    username: str 
    email: str

app = FastAPI()
@app.post("/users", response_model=UserOut)
async def create_user(user: UserCreate):
    new_user = user
    return new_user

class ProductType(str, Enum):
    FOOD = "food"
    Daily = "daily"
    TOYS = "toys"

class ProductCreate(BaseModel):
    name: str
    price: float = Field(gt=0)
    stock: int
    status: ProductType

@app.post("/products")
async def create_product(product: ProductCreate):
    new_product = product
    return new_product