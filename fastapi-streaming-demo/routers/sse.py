from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
import time
import json

router = APIRouter(prefix="/sse", tags=["服务器发送事件(SSE)"])
@router.get("/chat-stream")
# question是查询参数，FastAPI会把 URL 中的 question值传给函数
async def chat_stream(request: Request, question: str = "你好"):
    async def event_generator():
        reply = f"你好，你问的是：'{question}'。这是一个模拟的流式回复："
        # 将字符串拆分成字符列表
        words = list(reply)
        # 末尾的两个换行符表示一条事件结束
        yield f"event: start\ndata: 开始生成回复...\n\n"
        for i, word in enumerate(words):
            if await request.is_disconnected():
                print("客户端断开连接")
                break
            await asyncio.sleep(0.1)
            # 发送消息事件，数据为 JSON 格式
            event_data = json.dumps( # 把字典序列化成 JSON 字符串
                {"word": word, "index": i, "is_end": False},
                ensure_ascii=False
            )
            yield f"event: message\ndata: {event_data}\n\n"
        # 发送结束事件
        yield f"event: end\ndata: 回复生成完毕\n\n"
    return StreamingResponse(
        content=event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache", # 要求中间环节不要缓存流内容
            "Connection": "keep-alive", # 表示连接保持开放以持续发送数据
            "X-Accel-Buffering": "no", # 禁用 Nginx 缓冲
        }
    )

        
        