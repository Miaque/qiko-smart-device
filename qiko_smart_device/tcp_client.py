import asyncio
import logging
import os
import socket
import webbrowser
from asyncio import Lock
from typing import Optional

from config import app_config
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


class TCPConnection:
    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.lock = Lock()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((socket.error, ConnectionError)),
        before_sleep=before_sleep_log(logger, logging.ERROR),
        reraise=True,
    )
    async def connect(self):
        async with self.lock:
            if self.connected:
                return

            try:
                if self.socket:
                    self.socket.close()

                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                await asyncio.get_event_loop().sock_connect(
                    self.socket, (app_config.BEMFA_URL, app_config.BEMFA_PORT)
                )

                # 发送订阅指令
                substr = f"cmd=1&uid={app_config.BEMFA_UID}&topic={app_config.BEMFA_TOPIC}\r\n"
                await asyncio.get_event_loop().sock_sendall(
                    self.socket, substr.encode("utf-8")
                )

                self.connected = True
                logger.info("TCP连接成功")

            except Exception as e:
                self.connected = False
                logger.error(f"TCP连接失败: {e}")
                raise

    async def disconnect(self):
        async with self.lock:
            if self.socket:
                self.socket.close()
            self.connected = False
            self.socket = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type((socket.error, ConnectionError)),
        before_sleep=before_sleep_log(logger, logging.ERROR),
    )
    async def send(self, data: str):
        if not self.connected:
            await self.connect()
        try:
            await asyncio.get_event_loop().sock_sendall(
                self.socket, data.encode("utf-8")
            )
        except Exception as e:
            self.connected = False
            logger.error(f"发送数据失败: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type((socket.error, ConnectionError)),
        before_sleep=before_sleep_log(logger, logging.ERROR),
    )
    async def recv(self, buffer_size: int = 1024) -> bytes:
        if not self.connected:
            await self.connect()
        try:
            data = await asyncio.get_event_loop().sock_recv(self.socket, buffer_size)
            if not data:  # 如果接收到空数据，表示连接已断开
                self.connected = False
                raise ConnectionError("连接已断开")
            return data
        except Exception as e:
            self.connected = False
            logger.error(f"接收数据失败: {e}")
            raise

    async def start_ping(self):
        """启动心跳任务"""
        while True:
            try:
                await self.send("ping\r\n")
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"心跳发送失败: {e}")
                await asyncio.sleep(2)

    async def start_message_handler(self):
        """启动消息处理任务"""
        while True:
            try:
                recv_data = await self.recv(1024)
                message = recv_data.decode("utf-8").strip()
                logger.info(f"收到消息: {message}")

                if message.startswith("cmd=2"):
                    params = dict(item.split("=") for item in message.split("&"))
                    cmd, uid, topic, msg = (
                        params.get("cmd"),
                        params.get("uid"),
                        params.get("topic"),
                        params.get("msg"),
                    )
                    logger.info(
                        f"解析消息: cmd={cmd}, uid={uid}, topic={topic}, msg={msg}"
                    )

                    if msg == "on":
                        webbrowser.open("https://chat.qkos.cn")
                    elif msg == "off":
                        os.system("taskkill /f /im chrome.exe")

            except Exception as e:
                logger.error(f"消息处理错误: {e}")
                await asyncio.sleep(2)


# 创建全局连接实例
tcp_conn = TCPConnection()
