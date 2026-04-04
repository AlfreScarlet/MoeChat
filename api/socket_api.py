import socket
import threading
import asyncio
from utils.pysilero import VADIterator
from utils.log import logger
from io import BytesIO
import core.chat_core as chat_core
import soundfile as sf
import numpy as np
import time
from core.chat_core import current_task


async def chat_proxy(msg: str, client_socket: socket.socket):
    loop = asyncio.get_event_loop()
    try:
        async for chunk in chat_core.text_llm_tts_v3(msg=msg):
            await loop.sock_sendall(client_socket, chunk)
    except (BrokenPipeError, ConnectionResetError, OSError):
        logger.info("客户端断开连接")
        raise

async def stop():
    """取消当前正在进行的任务"""
    if current_task["processor"]:
        logger.info("取消之前的任务...")
        current_task["processor"].cancel()
    if current_task["llm"] and not current_task["llm"].done():
        current_task["llm"].cancel()
        try:
            await current_task["llm"]
        except (asyncio.CancelledError, Exception):
            pass
    if current_task["tts"] and not current_task["tts"].done():
        current_task["tts"].cancel()
        try:
            await current_task["tts"]
        except (asyncio.CancelledError, Exception):
            pass

async def handle_client(client_socket: socket.socket):
    """处理客户端连接，确保完整接收消息"""
    vad_iterator = VADIterator(speech_pad_ms=400)
    current_speech = []
    current_speech_tmp = []
    data_tmp = b""
    status = False
    audio_len = 0
    last_msg_time = time.time()
    loop = asyncio.get_event_loop()
    client_socket.setblocking(False)
    # 发送欢迎消息
    while True:
        # 检查缓存数据是否存在<|end|>结束符号
        if data_tmp.find(b"<|end|>") == -1:
            # 接收完整消息
            try:
                data = await loop.sock_recv(client_socket, 1024)
                if not data:  # 客户端正常关闭
                    client_socket.close()
                    logger.info(f"客户端断开：{client_socket}")
                    await stop()
                    return
                data_tmp += data
            except (ConnectionResetError, OSError) as e:
                client_socket.close()
                logger.info(f"客户端异常断开：{e}")
                await stop()
                return
            continue

        complate_data = data_tmp.split(b"<|end|>")[0]
        data_tmp = data_tmp.split(b"<|end|>")[1]

        if b"<|me|>" in complate_data:
            complate_data = complate_data.replace(b"<|me|>", b"")
            try:
                asyncio.create_task(chat_proxy(msg=complate_data.decode("utf-8"), client_socket=client_socket))
            except Exception as e:
                logger.error(f"chat_proxy 错误: {e}")
                # return
            continue
        elif b"<|audio|>" in complate_data:
            complate_data = complate_data.replace(b"<|audio|>", b"")
        else:
            continue

        # print(f"[客户端 {client_address}] {message}")
        # data = json.loads(data)
        # if data["type"] == "asr":
        # audio_data = base64.urlsafe_b64decode(str(data["data"]).encode("utf-8"))
        samples = np.frombuffer(complate_data[:len(complate_data) - len(complate_data) % 2], dtype=np.int16)
        current_speech_tmp.append(samples)
        audio_len += len(samples)
        if audio_len < 960:
            continue
        else:
            audio_len = 0
        resampled = np.concatenate(current_speech_tmp.copy())
        resampled = (resampled / 32768.0).astype(np.float32)
        current_speech_tmp = []
        
        for speech_dict, speech_samples in vad_iterator(resampled):
            if "start" in speech_dict:
                if time.time() - last_msg_time > 1.5:
                    current_speech = []
                status = True
                # print("开始说话")
                try:
                    # 发送打断信号
                    client_socket.sendall(f"<|start|><|end|>".encode("utf-8"))
                    await stop()
                except (BrokenPipeError, ConnectionResetError, OSError):
                    client_socket.close()
                    logger.info("客户端断开连接")
                    await stop()
                    return
                pass
            if status:
                current_speech.append(speech_samples)
            else:
                continue
            is_last = "end" in speech_dict
            if is_last:
                last_msg_time = time.time()
                # print("结束说话")
                status = False
                combined = np.concatenate(current_speech)
                audio_bytes = b""
                with BytesIO() as buffer:
                    sf.write(
                        buffer,
                        combined,
                        16000,
                        format="WAV",
                        subtype="PCM_16",
                    )
                    buffer.seek(0)
                    audio_bytes = buffer.read()  # 完整的 WAV bytes
                    res_text = chat_core.asr(audio_bytes)
                    if res_text:
                        try:
                            client_socket.sendall(f"<|me|>{res_text}<|end|>".encode("utf-8"))
                            asyncio.create_task(chat_proxy(msg=res_text, client_socket=client_socket))
                            # await chat_proxy(msg=res_text, client_socket=client_socket)
                        except (BrokenPipeError, ConnectionResetError, OSError):
                            client_socket.close()
                            logger.info("客户端断开连接")
                            await stop()
                            return
                # current_speech = []  # 清空当前段落


def start_socket_server(host: str, port: int):
    """启动服务器"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 端口复用
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(100)
    logger.info(f"socket_asr服务启动，监听 {host}:{port}...")
    
    try:
        while True:
            client_socket, addr = server_socket.accept()
            logger.info(f"新连接：{addr}")

            threading.Thread(
                target=lambda: asyncio.run(handle_client(client_socket)),
                args=(),
                daemon=True
            ).start()

    except KeyboardInterrupt:
        logger.info("服务器正在关闭...")
    finally:
        server_socket.close()