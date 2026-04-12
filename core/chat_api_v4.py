import asyncio
import time

from collections.abc import AsyncGenerator
from utils.log import logger
from utils.llm_request import llm_request_stream
from utils.split_text import remove_parentheses_content_and_split_v2
from core.tools import tts_task as TTS_TASK
from core.tools import TTSData, get_emotion_reference
from services.assistant_service import AssistantService


assistant_service = AssistantService()


async def text_2_tts(
    text_tts_queue: asyncio.Queue, 
    res_queue: asyncio.Queue,
):
    t1 = time.time()
    is_first = True
    try:
        while True:
            text = await asyncio.wait_for(text_tts_queue.get(), timeout=10)
            if not text:
                return
            ref_audio, ref_text = get_emotion_reference(text)
            if not ref_audio or not ref_text:
                return
            tts_data = TTSData(
                text=text,
                ref_audio=ref_audio,
                ref_text=ref_text,
            )
            if is_first:
                t1 = time.time()
            async for audio_chunk in TTS_TASK(tts_data, stream=True):
                if is_first:
                    logger.info(f"TTS首包耗时: {time.time() - t1:.3f}秒")
                    is_first = False
                if audio_chunk:
                    await asyncio.wait_for(res_queue.put({"type": "audio", "data": audio_chunk}), timeout=1)
    except asyncio.TimeoutError:
        logger.error("TTS任务超时")
    finally:
        try:
            await asyncio.wait_for(res_queue.put(None), timeout=1)
        except:
            pass

async def request_2_text(
    context: list[str], 
    text_tts_queue: asyncio.Queue, 
    res_queue: asyncio.Queue,
):
    full_text = ""
    tmp_text = ""
    is_first = True
    t1 = time.time()
    # 获取异步迭代器
    aiter = llm_request_stream(context).__aiter__()
    try:
        while True:
            text_chunk = await asyncio.wait_for(aiter.__anext__(), timeout=10)
            if not text_chunk:
                return
            full_text += text_chunk
            tmp_text += text_chunk
            await asyncio.wait_for(res_queue.put({"type": "text", "data": text_chunk}), timeout=10)
            tts_text, tmp_text = remove_parentheses_content_and_split_v2(tmp_text, is_first)
            if tts_text:
                await asyncio.wait_for(text_tts_queue.put(tts_text), timeout=1)
                if is_first:
                    logger.info(f"LLM首句耗时: {time.time() - t1:.3f}秒")
                    is_first = False
    except asyncio.TimeoutError:
        logger.error("LLM请求超时")
    
    finally:
        try:
            if tmp_text:
                await asyncio.wait_for(text_tts_queue.put(tmp_text), timeout=1)
            await asyncio.wait_for(text_tts_queue.put(None), timeout=1)
            if full_text.replace(" ", "").replace("\n", ""):
                await asyncio.wait_for(res_queue.put({"type": "complete", "data": full_text}), timeout=1)
        except:
            pass

async def text_llm_tts_v4(msg: str) -> AsyncGenerator[bytes, None]:
    """主处理函数（使用 asyncio.Lock，支持实时切换助手）"""
    agent = assistant_service.get_current_assistant()
    
    try:
        # 获取当前助手并验证有效性
        if not agent or not msg:
            logger.error("当前没有加载助手或消息为空")
            return
        
        # 防御性检查：验证 agent 对象有效性
        if not hasattr(agent, 'async_chat_lock') or not hasattr(agent, 'interrupted_lock'):
            logger.error("助手对象异常，缺少必要属性")
            return
        
        # 验证助手配置是否加载
        if not hasattr(agent, 'agent_config') or not agent.agent_config:
            logger.error("助手配置未加载")
            return

        await agent.async_chat_lock.acquire()
        async with agent.interrupted_lock:
            agent.interrupted = False  # 重置打断状态

        # 获取上下文
        context = await agent.get_msg_data(msg=msg)
        if not context:
            return 

        text_tts_queue = asyncio.Queue()
        res_queue = asyncio.Queue()
        
        # 启动文本处理协程
        text_task = asyncio.create_task(request_2_text(context, text_tts_queue, res_queue))
        tts_task = asyncio.create_task(text_2_tts(text_tts_queue, res_queue))

        while True:
            res = await asyncio.wait_for(res_queue.get(), timeout=10)
            if not res:
                break
            if res["type"] == "text":
                yield f"<|text|>{res['data']}<|end|>".encode("utf-8")  # 直接返回文本数据
            if res["type"] == "audio":
                yield b"<|audio|>" + res["data"] + b"<|end|>"  # 直接返回音频数据
            if res["type"] == "complete":
                agent.add_msg(res["data"])
            async with agent.interrupted_lock:
                if agent.interrupted:
                    logger.info("检测到打断信号，停止生成")
                    break
    
    except StopAsyncIteration:
        pass  # 正常结束，不处理
    except Exception as e:
        logger.error(f"消息处理异常退出: {e}")
    finally:
        yield f"<|complete|><|end|>".encode("utf-8")  # 发送完成标志
        # 取消未完成的任务并等待
        try:
            text_task.cancel()
            tts_task.cancel()
            await asyncio.gather(text_task, tts_task)
        except:
            pass
        try:
            if agent and agent.async_chat_lock.locked():
                agent.async_chat_lock.release()
        except:
            pass

            