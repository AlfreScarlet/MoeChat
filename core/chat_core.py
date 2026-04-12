import json
import time
import asyncio
import base64
import re
from typing import AsyncGenerator
import httpx
from fastapi.responses import JSONResponse
from models.dto.tts_request import tts_data
from utils import config as CConfig
from utils.sv import SV
from utils.socket_asr import ASRServer
from utils.log import logger
from utils.llm_request import llm_request_stream
from utils.split_text import remove_parentheses_content_and_split_v2
from core.meme_system import get_emotion_service
from services.assistant_service import AssistantService


assistant_service = AssistantService()


# 全局任务管理器
current_task = {"processor": None, "llm": None, "tts": None}


# 载入声纹识别模型
sv_pipeline: SV | None = None
if CConfig.config["Core"]["sv"]["is_up"]:
    sv_pipeline = SV(CConfig.config["Core"]["sv"])


from pydantic import BaseModel


class TTSData(BaseModel):
    """
    TTS数据类

    Attributes:
        text (str): 待合成的文本
        ref_audio (str): 参考音频路径
        ref_text (str): 参考文本
    """

    text: str
    ref_audio: str
    ref_text: str


class StreamProcessor:
    """
    流式处理LLM文本和TTS音频的处理器
    """

    def __init__(self, emotion_processed: bool = False):
        # 全部消息，ai可能回复多条语句
        self.full_msg: list[str] = []

        # 创建三个队列
        self.res_queue: asyncio.Queue[TTSData | str] = asyncio.Queue()  # TTS文本队列
        self.audio_queue = asyncio.Queue()  # TTS音频队列
        self.text_queue = asyncio.Queue()  # 流式文本输出队列

        # 缓存不完整的句子
        self.sentence_buffer = ""

        # 创建标志，用于记录任务是否已完成
        self.llm_done = False
        self.tts_done = False

        # 存储待合成的句子
        self.pending_sentences = []

        # 标记是否首句
        self.is_first_msg = True
        # 标记是否需要处理表情包
        self.emotion_processed = emotion_processed

        # 取消标志
        self.cancelled = False

        # 错误信息
        self.error_message: str | None = None

    def cancel(self):
        """取消并清空所有队列"""
        self.cancelled = True
        while not self.res_queue.empty():
            try:
                self.res_queue.get_nowait()
            except:
                break
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except:
                break
        while not self.text_queue.empty():
            try:
                self.text_queue.get_nowait()
            except:
                break
        self.pending_sentences.clear()

    async def handle_text_stream(self, text_task):
        """
        处理来自LLM的文本流
        """
        msg_type, content = text_task

        if msg_type == "text" and content:
            await self._process_text_chunk(content)

        elif msg_type == "done":
            self.llm_done = True
            await self._process_remaining_text()
            await self.res_queue.put("DONE_DONE")

        elif msg_type == "error":
            # 标记任务失败，不抛出异常避免重复日志
            self.llm_done = True
            self.error_message = content
            await self.res_queue.put("DONE_DONE")

    def _get_emotion(self, msg: str) -> str | None:
        """查询文字中的情感字段"""
        agent = assistant_service.get_current_assistant()
        if not agent:
            logger.error("[错误] 当前没有加载助手")
            return None
        res = re.findall(r"\[(.*?)\]", msg)
        if len(res) > 0:
            match = res[-1]
            if match and agent.agent_config.gsvSetting.extraRefAudio:
                if match in agent.agent_config.gsvSetting.extraRefAudio:
                    return match

    async def _process_text_chunk(self, content):
        """
        处理文本块
        """
        # 将新文本添加到缓冲区
        self.sentence_buffer += content

        # 对文本进行切句
        message_chunk, self.sentence_buffer = remove_parentheses_content_and_split_v2(
            self.sentence_buffer, self.is_first_msg
        )

        # 只处理完整文本块，否则跳过
        if len(message_chunk) == 0:
            return

        self.is_first_msg = False
        self.full_msg.append(message_chunk)

        # 检查情绪标签并获取参考音频
        ref_audio, ref_text = self._get_emotion_reference(message_chunk)

        # 添加到待合成列表
        self.pending_sentences.append(message_chunk)

        # 发送到tts队列，进行语音合成
        await self.res_queue.put(
            TTSData(
                text=message_chunk,
                ref_audio=ref_audio,
                ref_text=ref_text,
            )
        )

    async def _process_remaining_text(self):
        """
        处理缓存的剩余文本（即没有结尾符号的情况）
        """
        if len(self.sentence_buffer) > 0:
            self.full_msg.append(self.sentence_buffer)
            self.pending_sentences.append(self.sentence_buffer)

            # 检查情绪标签并获取参考音频
            ref_audio, ref_text = self._get_emotion_reference(self.sentence_buffer)

            # 发送到tts队列，进行语音合成
            await self.res_queue.put(
                TTSData(
                    text=self.sentence_buffer,
                    ref_audio=ref_audio,
                    ref_text=ref_text,
                )
            )

    def _get_emotion_reference(self, text: str) -> tuple[str, str]:
        """
        根据文本中的情绪标签获取参考音频和文本
        """
        agent = assistant_service.get_current_assistant()
        if not agent:
            logger.error("[错误] 当前没有加载助手")
            return "", ""
        emotion = self._get_emotion(text)

        ref_audio = ""
        ref_text = ""

        if emotion and emotion in agent.agent_config.gsvSetting.extraRefAudio.keys():
            ref_audio = agent.agent_config.gsvSetting.extraRefAudio[emotion][0]
            ref_text = agent.agent_config.gsvSetting.extraRefAudio[emotion][1]

        return ref_audio, ref_text

    async def handle_audio_stream(self, audio_task):
        """
        处理来自TTS的音频流
        """
        audio_item = await audio_task

        if audio_item == "DONE_DONE":
            self.tts_done = True

        elif audio_item is not None:
            # 当有音频数据时，将其与最早的待处理文本配对
            sentence_to_send = (
                self.pending_sentences.pop(0) if self.pending_sentences else ""
            )

            # 发送配对的文本和音频数据
            response_data = {
                "message": sentence_to_send,
                "file": audio_item,
                "done": False,
            }
            yield f"data: {json.dumps(response_data, ensure_ascii=False)}\n\n"

    def create_final_response(self):
        """
        创建最终响应数据
        """
        # 处理表情包系统,在创建最终响应前处理
        if self.emotion_processed and len(self.full_msg) > 0 and self.full_msg[0]:
            try:

                emotion_service = get_emotion_service()

                if not emotion_service.is_healthy():
                    logger.info("[表情包系统] 初始化表情包服务...")
                    emotion_service.initialize()

                meme_sse_response = emotion_service.process_llm_response(
                    self.full_msg[0]
                )
                if meme_sse_response:
                    logger.info("[表情包系统] 发送表情包到前端")
                    yield meme_sse_response

            except ImportError:
                logger.info("[表情包系统] 表情包模块未安装")
            except Exception as e:
                logger.info(f"[表情包系统] 处理表情包时发生错误：{e}")

        yield f"""data: {
            json.dumps({
            'message': ''.join(self.full_msg) if self.full_msg else '',
            'file': '',
            'done': True,
        }, ensure_ascii=False)
        }\n\n"""


async def gptsovits_tts(data: dict) -> AsyncGenerator[bytes, None]:
    """
    调用gptsovits进行语音合成(流式请求+流式返回原始bytes)

    Parameters:
        data (dict): 符合gptsovits的语音合成参数

    Yields:
        bytes: 音频数据块
    """
    async with httpx.AsyncClient() as client:
        try:
            async with client.stream(
                "POST", CConfig.config["GSV"]["api"], json=data, timeout=10
            ) as response:
                if response.status_code != 200:
                    logger.error(
                        f"[错误]tts语音合成失败！！！状态码: {response.status_code}"
                    )
                    logger.error(data)
                    response_text = await response.aread()
                    logger.error(response_text)
                    return

                # 直接流式读取原始bytes
                async for chunk in response.aiter_bytes():
                    if chunk:
                        yield chunk

        except Exception as e:
            logger.error(f"[错误]tts语音合成失败！！！ 错误信息: {e}")
            logger.error(data)


async def tts_task(tts_data: TTSData, stream=None) -> AsyncGenerator[bytes, None]:
    """
    构建tts任务

    Parameters
        tts_data : list
            包含参考音频、参考文本和合成文本的列表
    """
    agent = assistant_service.get_current_assistant()
    if not agent:
        logger.error("[错误] 当前没有加载助手")
        return

    msg = tts_data.text
    msg = re.sub(r"\(.*?\)|（.*?）|【.*?】|\[.*?\]|\{.*?\}", "", msg)
    msg = msg.replace(" ", "").replace("\n", "")
    # msg = clear_text(tts_data.text)
    if len(msg) == 0:
        return
    ref_audio = tts_data.ref_audio
    ref_text = tts_data.ref_text
    logger.info(f"[tts文本]{msg}")
    data = {
        "text": msg,
        "text_lang": agent.agent_config.gsvSetting.textLang,
        "ref_audio_path": agent.agent_config.gsvSetting.refAudioPath,
        "prompt_text": agent.agent_config.gsvSetting.promptText,
        "prompt_lang": agent.agent_config.gsvSetting.promptLang,
        "seed": agent.agent_config.gsvSetting.seed,
        "top_k": agent.agent_config.gsvSetting.topK,
    }
    if stream:
        data["streaming_mode"] = 2
        data["media_type"] = "raw"
        data["text_split_method"] = "cut0"
    else:
        data["batch_size"] = agent.agent_config.gsvSetting.batchSize
    if ref_audio:
        data["ref_audio_path"] = ref_audio
        data["prompt_text"] = ref_text
    try:
        async for audio_chunk in gptsovits_tts(data):
            yield audio_chunk
    except:
        return


async def start_tts(res_queue: asyncio.Queue, audio_queue: asyncio.Queue, processor=None, stream=None):
    """
    合并多个语音并返回

    Parameters
        res_queue : asyncio.Queue
            合成文本队列
        audio_queue : asyncio.Queue
            合成音频队列
        processor : StreamProcessor
            处理器实例，用于检查取消状态
    """
    logger.info("开始合成语言...")

    while True:
        # 检查是否被取消
        if processor and processor.cancelled:
            await audio_queue.put("DONE_DONE")
            logger.info("TTS任务被取消...")
            break

        try:
            item: TTSData = await res_queue.get()
            if item == "DONE_DONE":
                await audio_queue.put("DONE_DONE")
                logger.info("TTS任务完成...")
                break

            elif not item.text:
                continue

            logger.info(f"正在合成: {item.text[:10]}...")
            
            async for audio_data in tts_task(item, stream=stream):
            # if stream:
            #     audio_data = await tts_task(item, stream=True)
            # else:
            #     audio_data = await tts_task(item)

                if audio_data is None:
                    logger.error(f"TTS处理出错，发送空音频以跳过阻塞: {item.text[:10]}...")
                    continue

                if stream:
                    await audio_queue.put(audio_data)
                else:
                    encode_data = base64.b64encode(audio_data).decode("utf-8")
                    await audio_queue.put(encode_data)

        except Exception as e:
            logger.error(f"TTS循环发生未知错误: {e}", exc_info=True)
            continue


# asr功能
def asr(audio_data: bytes):
    """
    语音识别

    Parameters
        audio_data : bytes
            语音数据

    Returns
        str: 识别结果文本
    """
    global sv_pipeline

    if sv_pipeline:
        if not sv_pipeline.check_speaker(audio_data):
            return None

    asrServer = ASRServer()
    return asrServer.asr(audio_data)


async def start_llm_task(
    msg: list,
    text_queue: asyncio.Queue,
    processor=None,
):
    """
    将消息发送到大语言模型(LLM)并处理返回的流式响应

    Args:
        msg: 消息列表
        text_queue: 文本流式输出队列
        processor: StreamProcessor实例，用于检查取消状态
    """

    start_time = time.time()
    logger.info("[LLM]：开始处理")

    try:
        # 标记第一次打印时间
        first_print_time_flag = True

        async for line in llm_request_stream(msg):
            # 检查是否被取消
            if processor and processor.cancelled:
                logger.info("[LLM]：任务被取消")
                break

            try:
                if first_print_time_flag:
                    logger.info(f"[大模型延迟]{time.time() - start_time:.3f}s")
                    first_print_time_flag = False

                # 立即将新文本发送到文本队列（流式输出）
                await text_queue.put(("text", line))

            except Exception as e:
                logger.error(f"[错误]：{e}", exc_info=True)
                continue

        # 发送完成信号

        await text_queue.put(("done", None))

    except Exception as e:
        logger.error(f"无法链接到LLM服务器: {e}", exc_info=True)
        await text_queue.put(("error", str(e)))
        return JSONResponse(status_code=400, content={"message": "无法链接到LLM服务器"})


async def text_llm_tts(params: tts_data):
    """
    主处理函数：同时处理LLM流式文本输出和TTS音频合成
    文字和语音在同一个chunk输出
    """
    global current_task

    # 取消之前的任务
    if current_task["processor"]:
        logger.info("取消之前的任务...")
        current_task["processor"].cancel()
        if current_task["llm"] and not current_task["llm"].done():
            current_task["llm"].cancel()
        if current_task["tts"] and not current_task["tts"].done():
            current_task["tts"].cancel()

    agent = assistant_service.get_current_assistant()
    if not agent:
        logger.error("[错误] 当前没有加载助手")
        return
    # 获取agent内容
    msg_list_for_llm = await agent.get_msg_data(params.msg[-1]["content"])

    # 初始化处理器
    processor = StreamProcessor()

    # 创建LLM和TTS任务
    llm_task = asyncio.create_task(
        start_llm_task(msg_list_for_llm, processor.text_queue, processor)
    )
    tts_task = asyncio.create_task(
        start_tts(processor.res_queue, processor.audio_queue, processor)
    )

    # 保存当前任务
    current_task["processor"] = processor
    current_task["llm"] = llm_task
    current_task["tts"] = tts_task

    try:
        while True:
            # 检查是否被取消
            if processor.cancelled:
                # agent写入上下文、日记
                if processor.full_msg:
                    agent.add_msg("".join(processor.full_msg))
                break

            try:
                # 使用 asyncio.wait 同时监听多个队列
                text_task = asyncio.create_task(processor.text_queue.get())
                audio_task = asyncio.create_task(processor.audio_queue.get())

                done, pending = await asyncio.wait(
                    [text_task, audio_task],
                    return_when=asyncio.FIRST_COMPLETED,
                    timeout=0.1,
                )
                # 当获取到任一任务完成时，取消另一个任务
                for task in pending:
                    task.cancel()

                # 处理完成的任务
                for task in done:
                    if task == text_task:
                        await processor.handle_text_stream(task)

                    elif task == audio_task:
                        async for response in processor.handle_audio_stream(task):
                            yield response

                # 检查是否所有任务都完成
                if processor.llm_done and processor.tts_done:
                    # 发送最终的完成消息
                    for final_response in processor.create_final_response():
                        yield final_response
                    # agent写入上下文、日记
                    agent.add_msg("".join(processor.full_msg))
                    break

            except asyncio.TimeoutError:
                # 检查任务是否完成
                if llm_task.done() and tts_task.done():
                    break
                continue

            except Exception as e:
                logger.error(f"处理数据时出错: {e}", exc_info=True)
                error_response = {"type": "error", "data": str(e), "done": True}
                yield f"data: {json.dumps(error_response, ensure_ascii=False)}\n\n"
                break
    finally:
        # 清理当前任务引用
        if current_task["processor"] == processor:
            current_task["processor"] = None
            current_task["llm"] = None
            current_task["tts"] = None


async def text_llm_tts_v2(params: tts_data):
    """
    主处理函数：同时处理LLM流式文本输出和TTS音频合成
    文字和语音分别输出自己的chunk
    """
    global current_task

    # 取消之前的任务
    if current_task["processor"]:
        logger.info("取消之前的任务...")
        current_task["processor"].cancel()
        if current_task["llm"] and not current_task["llm"].done():
            current_task["llm"].cancel()
        if current_task["tts"] and not current_task["tts"].done():
            current_task["tts"].cancel()

    agent = assistant_service.get_current_assistant()
    if not agent:
        logger.error("[错误] 当前没有加载助手")
        return
    # 获取agent内容
    msg_list_for_llm = await agent.get_msg_data(params.msg[-1]["content"])

    # 初始化处理器
    processor = StreamProcessor()

    # 创建LLM和TTS任务
    llm_task = asyncio.create_task(
        start_llm_task(msg_list_for_llm, processor.text_queue, processor)
    )
    tts_task_instance = asyncio.create_task(
        start_tts(processor.res_queue, processor.audio_queue, processor)
    )

    # 保存当前任务
    current_task["processor"] = processor
    current_task["llm"] = llm_task
    current_task["tts"] = tts_task_instance

    try:
        while True:
            # 检查是否被取消
            if processor.cancelled:
                final_response = {
                    "type": "complete",
                    "data": "".join(processor.full_msg) if processor.full_msg else "",
                    "done": True,
                }
                yield f"data: {json.dumps(final_response, ensure_ascii=False)}\n\n"
                # agent写入上下文、日记
                if processor.full_msg:
                    agent.add_msg("".join(processor.full_msg))
                break

            try:
                # 使用 asyncio.wait 同时监听多个队列
                text_task = asyncio.create_task(processor.text_queue.get())
                audio_task = asyncio.create_task(processor.audio_queue.get())

                done, pending = await asyncio.wait(
                    [text_task, audio_task],
                    return_when=asyncio.FIRST_COMPLETED,
                    timeout=0.1,
                )
                # 当获取到任一任务完成时，取消另一个任务
                for task in pending:
                    task.cancel()

                # 处理完成的任务
                for task in done:
                    if task == text_task:
                        msg_type, content = await text_task

                        # 处理文本流并进入TTS队列
                        await processor.handle_text_stream((msg_type, content))

                        # 发送文本数据给客户端
                        if msg_type == "text" and content:
                            text_response = {"type": "text", "data": content, "done": False}
                            yield f"data: {json.dumps(text_response, ensure_ascii=False)}\n\n"
                        elif msg_type == "error":
                            error_response = {
                                "type": "error",
                                "data": content,
                                "done": True,
                            }
                            yield f"data: {json.dumps(error_response, ensure_ascii=False)}\n\n"

                    elif task == audio_task:
                        audio_item = await audio_task

                        if audio_item == "DONE_DONE":
                            processor.tts_done = True
                        elif audio_item is not None:
                            # 单独发送音频数据
                            audio_response = {
                                "type": "audio",
                                "data": audio_item,
                                "done": False,
                            }
                            yield f"data: {json.dumps(audio_response, ensure_ascii=False)}\n\n"

                # 检查是否所有任务都完成
                if processor.llm_done and processor.tts_done:
                    # 发送最终的完成消息
                    final_response = {
                        "type": "complete",
                        "data": "".join(processor.full_msg) if processor.full_msg else "",
                        "done": True,
                    }
                    yield f"data: {json.dumps(final_response, ensure_ascii=False)}\n\n"

                    # agent写入上下文、日记
                    agent.add_msg("".join(processor.full_msg))
                    break

            except asyncio.TimeoutError:
                # 检查任务是否完成
                if llm_task.done() and tts_task_instance.done():
                    break
                continue

            except Exception as e:
                logger.error(f"处理数据时出错: {e}", exc_info=True)
                error_response = {"type": "error", "data": str(e), "done": True}
                yield f"data: {json.dumps(error_response, ensure_ascii=False)}\n\n"
                break
    finally:
        # 清理当前任务引用
        if current_task["processor"] == processor:
            current_task["processor"] = None
            current_task["llm"] = None
            current_task["tts"] = None


async def text_llm_tts_v3(msg: str):
    """
    主处理函数：同时处理LLM流式文本输出和TTS音频合成
    文字和语音分别输出自己的chunk
    socket接口专用
    """
    global current_task

    # 取消之前的任务
    if current_task["processor"]:
        logger.info("取消之前的任务...")
        current_task["processor"].cancel()
        if current_task["llm"] and not current_task["llm"].done():
            current_task["llm"].cancel()
        if current_task["tts"] and not current_task["tts"].done():
            current_task["tts"].cancel()

    agent = assistant_service.get_current_assistant()
    
    if not agent:
        logger.error("[错误] 当前没有加载助手")
        return
    # 获取agent内容
    msg_list_for_llm = await agent.get_msg_data(msg=msg)

    # 初始化处理器
    processor = StreamProcessor()

    # 初始化记时器
    is_first_msg = True
    is_first_audio = True
    first_data_time = time.time()

    # 创建LLM和TTS任务
    llm_task = asyncio.create_task(
        start_llm_task(msg_list_for_llm, processor.text_queue, processor)
    )
    tts_task_instance = asyncio.create_task(
        start_tts(processor.res_queue, processor.audio_queue, processor, stream=True)
    )

    # 保存当前任务
    current_task["processor"] = processor
    current_task["llm"] = llm_task
    current_task["tts"] = tts_task_instance

    try:
        while True:
            # 检查是否被取消
            if processor.cancelled:
                # 发送最终的完成消息
                yield b"<|complete|><|end|>"
                # agent写入上下文、日记
                if processor.full_msg:
                    agent.add_msg("".join(processor.full_msg))
                break

            try:
                # 使用 asyncio.wait 同时监听多个队列
                text_task = asyncio.create_task(processor.text_queue.get())
                audio_task = asyncio.create_task(processor.audio_queue.get())

                done, pending = await asyncio.wait(
                    [text_task, audio_task],
                    return_when=asyncio.FIRST_COMPLETED,
                    timeout=0.1,
                )
                # 当获取到任一任务完成时，取消另一个任务
                for task in pending:
                    task.cancel()

                # 处理完成的任务
                for task in done:
                    if task == text_task:
                        if is_first_msg:
                            logger.info(f"[大模型首句延迟]{time.time() - first_data_time:.3f}s")
                            first_data_time = time.time()
                            is_first_msg = False
                        msg_type, content = text_task.result()

                        # 处理文本流并进入TTS队列
                        await processor.handle_text_stream((msg_type, content))

                        # 发送文本数据给客户端
                        if msg_type == "text" and content:
                            yield f"<|text|>{content}<|end|>".encode("utf-8")

                    elif task == audio_task:
                        if is_first_audio:
                            logger.info(f"[TTS首包延迟]{time.time() - first_data_time:.3f}s")
                            is_first_audio = False
                        audio_item = audio_task.result()

                        if audio_item == "DONE_DONE":
                            processor.tts_done = True
                        elif audio_item is not None:
                            # 单独发送音频数据
                            yield b"<|audio|>" + bytes(audio_item) + b"<|end|>"

                # 检查是否所有任务都完成
                if processor.llm_done and processor.tts_done:
                    # 如果有错误，发送错误消息
                    if processor.error_message:
                        yield f"<|error|>{processor.error_message}<|end|>".encode("utf-8")
                    else:
                        # 发送最终的完成消息
                        yield b"<|complete|><|end|>"

                        # agent写入上下文、日记
                        agent.add_msg("".join(processor.full_msg))
                    break

            except asyncio.TimeoutError:
                # 检查任务是否完成
                if llm_task.done() and tts_task_instance.done():
                    break
                continue

            except Exception as e:
                logger.error(f"处理数据时出错: {e}", exc_info=True)
                break
    finally:
        # 清理当前任务引用
        if current_task["processor"] == processor:
            current_task["processor"] = None
            current_task["llm"] = None
            current_task["tts"] = None
