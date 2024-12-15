import os
import socket
import threading
import time
import webbrowser

from config import app_config
from fastapi import FastAPI


def connTCP():
    global tcp_client_socket
    # 创建socket
    tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # 连接服务器
        tcp_client_socket.connect((app_config.BEMFA_URL, app_config.BEMFA_PORT))
        # 发送订阅指令
        substr = f"cmd=1&uid={app_config.BEMFA_UID}&topic={app_config.BEMFA_TOPIC}\r\n"
        tcp_client_socket.send(substr.encode("utf-8"))
    except:
        time.sleep(2)
        connTCP()


# 心跳
def Ping():
    # 发送心跳
    try:
        keeplive = "ping\r\n"
        tcp_client_socket.send(keeplive.encode("utf-8"))
    except:
        time.sleep(2)
        connTCP()
    # 开启定时，30秒发送一次心跳
    t = threading.Timer(30, Ping)
    t.start()


connTCP()
Ping()

app = FastAPI()


@app.get("/")
def index():
    return {"message": "Hello World"}


while True:
    # 接收服务器发送过来的数据
    recvData = tcp_client_socket.recv(1024)
    if len(recvData) != 0:
        message = recvData.decode("utf-8")
        print("recv:", message)
        # 清洗多余的换行符，并解析
        message = message.strip()
        if message.startswith("cmd=2"):
            cmd = message.split("&")[0].split("=")[1]
            uid = message.split("&")[1].split("=")[1]
            topic = message.split("&")[2].split("=")[1]
            msg = message.split("&")[3].split("=")[1]
            print(cmd, uid, topic, msg)

            if msg == "on":
                default = webbrowser.get()
                print(default)
                # 显示打开系统默认浏览器
                webbrowser.open("https://chat.qkos.cn")
            elif msg == "off":
                # 关闭系统默认浏览器
                os.system("taskkill /f /im chrome.exe")
    else:
        print("conn err")
        connTCP()
