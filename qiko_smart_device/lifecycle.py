import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from tcp_client import tcp_conn

logger = logging.getLogger(__name__)


async def start_background_tasks():
    """启动后台任务"""
    await tcp_conn.connect()

    # 创建并返回后台任务
    ping_task = asyncio.create_task(tcp_conn.start_ping())
    message_task = asyncio.create_task(tcp_conn.start_message_handler())

    return ping_task, message_task


async def cleanup_background_tasks(tasks):
    """清理后台任务"""
    for task in tasks:
        task.cancel()

    try:
        for task in tasks:
            await task
    except asyncio.CancelledError:
        pass

    await tcp_conn.disconnect()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("应用启动")

    # 启动后台任务
    background_tasks = await start_background_tasks()

    yield

    # 清理后台任务
    await cleanup_background_tasks(background_tasks)
    logger.info("应用关闭")
