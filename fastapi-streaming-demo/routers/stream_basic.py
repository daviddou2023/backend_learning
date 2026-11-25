# 用于把一组相关路由组织在一起
from fastapi import APIRouter
# StreamingResponse: 响应内容可以边生成边发送
from fastapi.responses import StreamingResponse
import asyncio
import time

""" 1. 创建路由组 """
# prefix的内容会加在每个接口路径前，tags用于给/docs文档分组
router = APIRouter(prefix="/stream/basic", tags=["基础流式输出"])

""" 2. 定义接口 """
# 把接口注册到路由组里，后续再注册到主应用，方便管理
@router.get("/text-stream") # 调用此接口时，函数会返回一个 StreamingResponse
async def text_stream():
    """ 3. 定义异步生成器 """
    async def data_generator():
        for i in range(1, 11):
            await asyncio.sleep(1.0)
            # yield 暂时交出一个结果，之后生成器可以继续运行并交出下一行
            yield f"这是第 {i} 行数据，当前时间：{time.strftime('%H:%M:%S')}\n"

    """ 4. 把生成器交给响应对象 """
    return StreamingResponse(
        content=data_generator(),
        media_type="text/plain; charset=utf-8" # 响应时UTF-8编码的纯文本
    )

