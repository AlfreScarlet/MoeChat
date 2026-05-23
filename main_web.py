import asyncio
from init_server import init
from web.src.router.router import app
import uvicorn
from threading import Thread
from api.socket_api import start_socket_server
from server_settings import (
    get_socket_host,
    get_socket_port,
    get_web_host,
    get_web_port,
)


def start_server():
    web_host = get_web_host()
    web_port = get_web_port()
    socket_host = get_socket_host()
    socket_port = get_socket_port()

    # 等待初始化完成
    asyncio.get_event_loop().run_until_complete(init())
    # 启动socket服务
    Thread(
        target=start_socket_server,
        args=(socket_host, socket_port),
        daemon=True,
    ).start()
    # 启动web服务，应该在最后
    uvicorn.run(app, host=web_host, port=web_port)


if __name__ == "__main__":
    start_server()
