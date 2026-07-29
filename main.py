import uuid

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request

from app.agent.api.routers.query_router import query_router
from app.core.context import request_id_ctx_var
from app.agent.api.lifespan import lifespan
from app.core.log import logger

load_dotenv()
app = FastAPI(lifespan=lifespan, title="Data-Agent" ,description="一个用于查询结构化数据的智能体")

app.include_router(query_router)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    # 调用路径函数之前
    request_id_ctx_var.set(uuid.uuid4())
    # 调用路径函数
    response = await call_next(request)
    # 调用路径函数之后
    return response

if __name__ == '__main__':
    logger.info("SQL 查询服务启动中...")
    # 启动uvicorn服务，绑定本地IP和8000端口，关闭自动重载（生产环境建议用workers多进程）
    uvicorn.run(
        app=app,
        host="127.0.0.1",  # 仅本地访问，生产环境改为0.0.0.0（允许所有IP访问）
        port=7000  # 服务端口
    )