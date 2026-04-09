import re
import httpx


from utils import config as CConfig
from services.assistant_service import AssistantService
from utils.log import logger
from pydantic import BaseModel
from typing import AsyncGenerator


assistant_service = AssistantService()

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


def get_emotion_reference(text: str) -> tuple[str, str]:
        """
        根据文本中的情绪标签获取参考音频和文本
        """
        agent = assistant_service.get_current_assistant()
        if not agent:
            logger.error("[错误] 当前没有加载助手")
            return "", ""
        
        # 防御性检查：验证 agent 配置
        if not hasattr(agent, 'agent_config') or not agent.agent_config:
            logger.error("[错误] 助手配置未加载")
            return "", ""
        
        if not hasattr(agent.agent_config, 'gsvSetting'):
            logger.error("[错误] 助手语音配置不存在")
            return "", ""
        res = re.findall(r"\[(.*?)\]", text)
        emotion = ""
        if len(res) > 0:
            match = res[-1]
            if match and agent.agent_config.gsvSetting.extraRefAudio:
                if match in agent.agent_config.gsvSetting.extraRefAudio:
                    emotion = match

        ref_audio = ""
        ref_text = ""

        if emotion and emotion in agent.agent_config.gsvSetting.extraRefAudio.keys():
            ref_audio = agent.agent_config.gsvSetting.extraRefAudio[emotion][0]
            ref_text = agent.agent_config.gsvSetting.extraRefAudio[emotion][1]
        else:
            ref_audio = agent.agent_config.gsvSetting.refAudioPath
            ref_text = agent.agent_config.gsvSetting.promptText

        return ref_audio, ref_text

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
    
    # 防御性检查：验证 agent 配置
    if not hasattr(agent, 'agent_config') or not agent.agent_config:
        logger.error("[错误] 助手配置未加载")
        return
    
    if not hasattr(agent.agent_config, 'gsvSetting'):
        logger.error("[错误] 助手语音配置不存在")
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