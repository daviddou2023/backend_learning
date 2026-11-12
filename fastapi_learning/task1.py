from fastapi import FastAPI
# 创建一个FastAPI应用示例
# app 是应用对象，后续会在它上面注册接口。运行服务器时，也会告诉 uvicorn：要运行哪个python模块中的哪个应用对象
from pydantic import BaseModel
app = FastAPI()

# 定义一个装饰器，把下面的函数注册成一个路由，假设服务运行在 http://127.0.0.1:8000，那么访问 http://127.0.0.1:8000/ 就会匹配这个路由
@app.get("/") # 表示这个路由接收 HTTP GET 请求
async def root():
    return {"messages": "Hello World"} # 函数返回一个python字典，FastAPI 会把它转换成 JSON响应


# 创建模拟数据列表，每一个元素是一个字典，只保留在python程序的内存中
books = [
    {"id": 1, "title": "三体", "author": "刘慈欣"},
    {"id": 2, "title": "红楼梦", "author": "曹雪芹"},
    {"id": 3, "title": "流浪地球", "author": "刘慈欣"},
]
# 定义服务端返回图书时的数据结构
class BookOut(BaseModel):
    id: int
    title: str
    author: str

# 将 get_all_books 注册为 GET /books 请求的路由函数
@app.get("/books")
async def get_all_books(author: str | None = None, skip: int = 0, limit: int = 10):
    result = books
    if author:
        result = [b for b in result if b["author"] == author] # 列表推导式，[要放进新列表的内容 for 临时变量 in 原列表 if 筛选条件]
    return result[skip : skip + limit]

@app.get("/books/{book_id}", response_model=BookOut, status_code=200) # book_id 是路径参数，表示这一段URL内容会作为参数传给下面的处理函数
async def get_book(book_id: int): # book_id :int 是 python的类型注解
    for book in books:
        if book["id"] == book_id: # GET /books/2 <--> {"id": 2, "title": "流浪地球", "author": "刘慈欣"}
            return book



# BookCreate 是一个 pydantic 模型，会校验收到的JSON字段，如果格式不符，FastAPI会自动拦截并返回422
class BookCreate(BaseModel):
    title: str
    author: str


# 将create_book函数注册为处理 POST /books 请求的路由
@app.post("/books", response_model=BookOut, status_code=201) # 增加路由参数
async def create_book(book: BookCreate):
    new_id = max(b["id"] for b in books) + 1
    new_book = {"id": new_id, "title": book.title, "author": book.author} # 组装新数据
    books.append(new_book) # 追加到原来的书库的末尾
    return new_book

@app.put("/books/{book_id}", response_model=BookOut, status_code=200)
async def update_book(book_id: int, book: BookCreate):
    for b in books:
        if b["id"] == book_id:
            b["title"] = book.title
            b["author"] = book.author
            return b
    return {"error": "Book not found"}

@app.delete("/books/{book_id}", status_code=204)
async def delete_book(book_id: int):
    for index, book in enumerate(books):
        if book["id"] == book_id:
            books.pop(index)
            return