from fastapi import FastAPI
import uvicorn
from routers import stream_basic, sse

app = FastAPI(title="流式输出演示")

# 把 stream_basic 模块中的 router路由对象注册到FastAPI应用中
app.include_router(stream_basic.router)
app.include_router(sse.router)

@app.get("/")
async def root():
    return {"message": "流式输出演示成功"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)