"""
Legacy experimental router.

This module is not mounted by web/src/router/router.py, so its HeWeather branch
is not part of the current main chat runtime. Treat it as an experimental
integration target until configuration, dependencies, static paths, and
end-to-end /api/stream_chat behavior are wired together in one PR.
"""

from fastapi import Query, APIRouter
from fastapi.responses import StreamingResponse, Response, RedirectResponse
from pydantic import BaseModel
import base64
import io
import json
from pydub import AudioSegment
import httpx
import filetype
import yaml
import os
import urllib.parse
from bs4 import BeautifulSoup
import random
import re
import math
import core.chat_core as chat_core
import time
from core.emotion.emotion_engine import EmotionEngine

router = APIRouter()

# --- 1. 读取配置文件 ---
with open("config.yaml", "r", encoding="utf-8") as f:
    config_data = yaml.safe_load(f)

# --- 2. 定义所有全局配置和状态变量 (只在这里定义一次) ---
agent_config = config_data.get("Agent", {})
llm_config = config_data.get("LLM", {})
heweather_cfg = config_data.get("HeWeather", {})
get_image_cfg = config_data.get("get_image", {})
memes_cfg = config_data.get("Memes", {})
pics_cfg = config_data.get("Pics", {})

# 读取所有功能开关
mood_system_enabled = agent_config.get("mood_system_enabled", False)
mood_persists = agent_config.get("mood_persists", False)
weather_feature_enabled = heweather_cfg.get("Is_on", False)
image_feature_enabled = get_image_cfg.get("enabled", False)
meme_feature_enabled = memes_cfg.get("turn_on", False)
pic_feature_enabled = pics_cfg.get("turn_on", False)


# 用于计算输入冲击的函数
emotion_engine = EmotionEngine(agent_config=agent_config, llm_config=llm_config)
mood_system_enabled = agent_config.get("mood_system_enabled", True)
emotion_profile_matrix = agent_config.get("emotion_profile_matrix", [])


conversation_history = []
CONTEXT_WINDOW_SIZE = 6

# 扫描并打印本地资源状态
STATIC_FILES_DIR = "F:/Moechatremote_client/static"  # 请确保这个路径是正确的
MEMES_BASE_DIR = os.path.join(STATIC_FILES_DIR, "memes")
PICS_BASE_DIR = os.path.join(STATIC_FILES_DIR, "pics")

print(f"[功能状态] 天气查询: {'启用' if weather_feature_enabled else '关闭'}")
print(f"[功能状态] 网络图片搜索: {'启用' if image_feature_enabled else '关闭'}")
print(f"[功能状态] 本地图片分享: {'启用' if pic_feature_enabled else '关闭'}")
if pic_feature_enabled:
    AVAILABLE_PICS = (
        [
            f
            for f in os.listdir(PICS_BASE_DIR)
            if os.path.isfile(os.path.join(PICS_BASE_DIR, f))
        ]
        if os.path.isdir(PICS_BASE_DIR)
        else []
    )
    if not AVAILABLE_PICS:
        print("           └─ [警告] 'pics' 文件夹是空的或不存在。")
    else:
        print(f"           └─ [加载成功] 发现 {len(AVAILABLE_PICS)} 个本地图片。")

print(f"[功能状态] 表情包: {'启用' if meme_feature_enabled else '关闭'}")

if meme_feature_enabled:
    VALID_MEME_FOLDERS = (
        [
            d
            for d in os.listdir(MEMES_BASE_DIR)
            if os.path.isdir(os.path.join(MEMES_BASE_DIR, d))
        ]
        if os.path.isdir(MEMES_BASE_DIR)
        else []
    )
    if not VALID_MEME_FOLDERS:
        print("           └─ [警告] 'memes' 文件夹内未找到任何主题子文件夹。")
    else:
        print(
            f"           └─ [加载成功] 发现 {len(VALID_MEME_FOLDERS)} 个表情包主题: {VALID_MEME_FOLDERS}"
        )

print("=" * 63 + "\n")


# 和风天气接口
async def get_heweather_dynamic(text: str) -> str:
    try:
        heweather_cfg = config_data.get("HeWeather", {})
        key = heweather_cfg.get("key")
        location_id = heweather_cfg.get("location_id")
        host = heweather_cfg.get("host", "devapi.qweather.com")

        if any(w in text for w in ["现在", "此刻", "今天"]):
            path, query_type = "now", "now"
        elif any(w in text for w in ["未来", "将来", "下一个"]) and any(
            d in text for d in ["3", "三"]
        ):
            path, query_type = "3d", "3d"
        elif any(w in text for w in ["未来", "将来", "下一个"]) and any(
            d in text for d in ["7", "七"]
        ):
            path, query_type = "7d", "7d"
        else:
            return "【天气信息】暂无法判断您请求的是哪天的天气，可尝试说“今天天气”、“未来3天天气”或“未来7天天气”。"

        url = f"https://{host}/v7/weather/{path}?location={location_id}"
        headers = {"X-QW-API-Key": key}

        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(url, headers=headers)
            data = res.json()

            print("\n===== [和风天气 API 原始JSON返回] =====")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("======================================\n")

        if data.get("code") != "200":
            return f"【天气信息】无法获取天气数据，API错误码: {data.get('code')}。"

        if query_type == "now" and "now" in data:
            now = data["now"]
            return f"【天气信息】当前天气：{now.get('text', '')}，气温{now.get('temp', '')}℃，体感温度{now.get('feelsLike', '')}℃，{now.get('windDir', '')}{now.get('windScale', '')}级，相对湿度{now.get('humidity', '')}%，降水量{now.get('precip', '0')}毫米。"

        elif "daily" in data:
            report_lines = []
            for d in data["daily"]:
                fxDate = d.get("fxDate", "")
                textDay = d.get("textDay", "")
                textNight = d.get("textNight", "")
                tempMin = d.get("tempMin", "")
                tempMax = d.get("tempMax", "")
                line = f"{fxDate}: 白天{textDay}/夜间{textNight}，{tempMin}~{tempMax}℃"
                report_lines.append(line)

            days_str = "\n".join(report_lines)
            days_count_char = query_type[0]
            return f"【天气信息】未来{days_count_char}天天气预报如下：\n{days_str}"
        else:
            return "【天气信息】未能从API获取到有效的天气详情。"

    except Exception as e:
        return f"【天气信息】请求过程中发生内部错误: {e}。"


# 图片搜索 URL 构造器
def build_image_search_url(keyword: str):
    get_image_cfg = config_data.get("get_image", {})
    engine = get_image_cfg.get("engine", "yandex")
    engine_urls = get_image_cfg.get("engines", {})
    if engine not in engine_urls:
        return None
    base_url = engine_urls[engine]
    encoded = urllib.parse.quote(keyword, safe="")
    return base_url + encoded


@router.get("/img_search")
async def img_search(q: str = Query(...)):
    try:
        url = build_image_search_url(q)
        headers = {"User-Agent": "Mozilla/5.0"}
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        img_urls = []
        a_tags = soup.find_all("a", class_="iusc")
        for a in a_tags:
            meta = a.get("m")
            if not meta:
                continue
            try:
                data = json.loads(meta)
                murl = data.get("murl")
                if murl and murl.startswith("http"):
                    img_urls.append(murl)
            except:
                continue
            if len(img_urls) >= 4:
                break
        if not img_urls:
            return {"error": "未找到图片"}
        return {"images": img_urls}
    except Exception as e:
        return {"error": str(e)}


class AudioData(BaseModel):
    audio: str


@router.post("/audio")
async def process_audio(data: AudioData):
    try:
        header, encoded = (
            data.audio.split(",", 1) if "," in data.audio else ("", data.audio)
        )
        audio_bytes = base64.b64decode(encoded)
        kind = filetype.guess(audio_bytes)
        if kind is None:
            return {"error": "无法识别的音频格式"}
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=kind.extension)
        audio = audio.set_frame_rate(16000).set_channels(1)
        buf = io.BytesIO()
        audio.export(buf, format="wav")
        buf.seek(0)
        text = chat_core.asr(buf.read())
        user_text = text and text.strip()
        if not user_text:
            return {"error": "ASR未返回有效文本"}
        return {"text": user_text}
    except Exception as e:
        return {"error": str(e)}


# 图片处理函数
async def process_image_tag(tag: str):
    keyword = re.findall(r"\{image:(.+?)\}", tag)
    if not keyword:
        return
    kw = keyword[0].strip()
    kw_for_search = kw.replace(" ", "")
    if not kw_for_search:
        return
    print(f"[图片请求]：'{kw}' (搜索使用: '{kw_for_search}')")
    img_url = (
        f"http://127.0.0.1:8001/web/img_search?q={urllib.parse.quote(kw_for_search)}"
    )
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(img_url)
        data = res.json()
        if "images" in data and data["images"]:
            selected_image = random.choice(data["images"])
            yield f"data: {json.dumps({'file': None, 'message': f'{{img}}{selected_image}', 'done': False})}\n\n"
        else:
            yield f"data: {json.dumps({'file': None, 'message': f'[系统提示] 未找到关于“{kw}”的图片', 'done': False})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'file': None, 'message': f'[系统提示] 搜索“{kw}”的图片时接口错误', 'done': False})}\n\n"


# 表情包处理函数
async def process_meme_tag(tag: str):
    keyword = re.findall(r"\{meme:(.+?)\}", tag)
    if not keyword:
        return
    kw = keyword[0].strip()

    if kw not in VALID_MEME_FOLDERS:
        print(f"[表情包功能] 警告：LLM试图使用一个不存在的表情包关键词 '{kw}'")
        return

    try:
        meme_folder_path = os.path.join(MEMES_BASE_DIR, kw)
        meme_files = [
            f
            for f in os.listdir(meme_folder_path)
            if os.path.isfile(os.path.join(meme_folder_path, f))
        ]
        if not meme_files:
            print(f"[表情包功能] 警告：表情包文件夹 '{kw}' 是空的。")
            return

        random_meme = random.choice(meme_files)
        meme_url = f"/static/memes/{kw}/{random_meme}"
        print(f"[表情包功能] 发送表情包：{meme_url}")
        yield f"data: {json.dumps({'file': None, 'message': f'{{img}}{meme_url}', 'done': False})}\n\n"

    except Exception as e:
        print(f"[表情包功能] 处理表情包 '{kw}' 时发生错误: {e}")


# 发送随机本地图片的函数
async def send_random_pic():
    if not AVAILABLE_PICS:
        print(f"[本地图片功能] 警告：'pics' 文件夹是空的或不存在。")
        return
    try:
        random_pic_filename = random.choice(AVAILABLE_PICS)
        pic_url = f"/static/pics/{random_pic_filename}"
        print(f"[本地图片功能] 发送图片：{pic_url}")
        yield f"data: {json.dumps({'file': None, 'message': f'{{img}}{pic_url}', 'done': False})}\n\n"
    except Exception as e:
        print(f"[本地图片功能] 处理随机图片时发生错误: {e}")


# LLM流式响应处理器
async def process_llm_stream(
    response, image_feature_enabled, meme_feature_enabled, pic_feature_enabled
):
    async for line in response.aiter_lines():
        if not (line and line.startswith("data:")):
            continue
        content_str = line[len("data:") :].strip()
        try:
            llm_data = json.loads(content_str)
            if llm_data.get("done"):
                break
            message_chunk = llm_data.get("message", "")

            # ===== 修正：将正则表达式中的 pic 改为 pics =====
            sub_segments = re.split(
                r"(\{image:.*?\}|\{meme:.*?\}|\{pics:.*?\})", message_chunk
            )

            audio_has_been_sent = False

            for sub_seg in sub_segments:
                if not sub_seg:
                    continue

                if image_feature_enabled and sub_seg.startswith("{image:"):
                    async for item in process_image_tag(sub_seg):
                        yield item
                elif meme_feature_enabled and sub_seg.startswith("{meme:"):
                    async for item in process_meme_tag(sub_seg):
                        yield item
                elif pic_feature_enabled and sub_seg.startswith("{pics:"):
                    async for item in send_random_pic():
                        yield item
                else:
                    current_payload = llm_data.copy()
                    current_payload["message"] = sub_seg

                    if not audio_has_been_sent:
                        audio_has_been_sent = True
                    else:
                        current_payload["file"] = None

                    yield f"data: {json.dumps(current_payload)}\n\n"

        except json.JSONDecodeError:
            yield line + "\n\n"


@router.get("/stream_chat")
async def stream_chat(text: str = Query(...)):
    async def audio_stream():
        mood_instruction = await emotion_engine.process_emotion(text)

        ai_full_response = ""  # 用于累积AI的完整回复

        try:
            chat_data = None  # 初始化chat_data，确保它在每个流程中都被定义

            # --- 分支一: “戳一戳”事件处理 (最高优先级) ---
            if text.startswith("{event:poke_"):
                print(f"[事件触发]: {text}")
                final_prompt = ""
                poke_meme = ""
                if mood_system_enabled:
                    print("[情绪系统] 戳一戳事件将根据当前情绪动态回应。")
                    # ...（此处是完整的、根据情绪值设定poke_meme和final_prompt的if/elif/else逻辑）
                else:
                    print("[情绪系统] 戳一戳事件使用预设彩蛋回应。")
                    # ...（此处是完整的、从poke_events字典中获取prompt和meme的逻辑）

                if final_prompt:
                    if meme_feature_enabled and poke_meme:
                        async for item in process_meme_tag(f"{{meme:{poke_meme}}}"):
                            yield item
                    chat_data = {"msg": [{"role": "system", "content": final_prompt}]}

            # --- 分支二: 天气功能处理 (第二优先级) ---
            elif weather_feature_enabled and any(kw in text for kw in ["天气", "气温"]):
                print("[天气功能触发]")
                weather_data_string = await get_heweather_dynamic(text)
                weather_system_prompt = (
                    "你是一个生活助手，也是一个天气播报员..."  # 省略完整prompt
                )
                if mood_system_enabled:
                    weather_system_prompt += mood_instruction
                content_for_llm = f"用户的原始问题是：“{text}”\n\n这是为你查询到的实时天气数据：“{weather_data_string}”\n\n请根据以上信息进行回复。"
                chat_data = {
                    "msg": [
                        {"role": "system", "content": weather_system_prompt},
                        {"role": "user", "content": content_for_llm},
                    ]
                }

            # --- 分支三: 常规对话流程 (最后执行) ---
            else:
                # 独立处理图片标签，不影响主对话流程
                async for item in process_image_tag(text):
                    yield item
                processed_text_for_llm = re.sub(r"(\{image:.*?\})", "", text).strip()

                if processed_text_for_llm:
                    # 第一部分: 角色与情绪指令
                    system_prompt = "你是一个AI助手。"
                    if mood_system_enabled:
                        system_prompt += mood_instruction

                    # 第二部分: 可用工具指令
                    tool_instructions = []
                    if image_feature_enabled:
                        tool_instructions.append(
                            "【网络图片搜索】: 当用户需要一张具体内容的图片时，你必须严格使用`{image:搜索关键词}`格式来调用。例如：`{image:一只可爱的英国短毛猫}`。"
                        )
                    if meme_feature_enabled and VALID_MEME_FOLDERS:
                        meme_keywords_str = ", ".join(VALID_MEME_FOLDERS)
                        tool_instructions.append(
                            f"【发送表情包】: 当你想用表情包表达情绪时，你必须严格使用`{{meme:关键词}}`格式来调用。可用的关键词有: {meme_keywords_str}。"
                        )
                    if pic_feature_enabled and AVAILABLE_PICS:
                        tool_instructions.append(
                            "【发送本地精美图片】: 当你想主动分享一张美丽的图片时，你必须严格使用`{pics:好看的图片}`这个固定标签。"
                        )

                    if tool_instructions:
                        system_prompt += "\n\n---【可用工具说明】---\n"
                        system_prompt += "你拥有以下工具，使用时必须严格遵守格式，不要进行任何形式的创造或修改：\n"
                        system_prompt += "\n".join(tool_instructions)

                    chat_data = {
                        "msg": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": processed_text_for_llm},
                        ]
                    }

            # --- 统一的API调用和流式处理 ---
            # 只有在前面的某个分支成功创建了chat_data后，才执行API调用
            if chat_data:
                async with httpx.AsyncClient(timeout=65.0) as client:
                    async with client.stream(
                        "POST", "http://127.0.0.1:8001/api/chat", json=chat_data
                    ) as response:
                        async for chunk in process_llm_stream(
                            response,
                            image_feature_enabled,
                            meme_feature_enabled,
                            pic_feature_enabled,
                        ):
                            yield chunk
                            # 累积回复
                            try:
                                data_str = chunk.decode("utf-8")
                                if data_str.startswith("data:"):
                                    json_data = json.loads(
                                        data_str[len("data:") :].strip()
                                    )
                                    message_piece = json_data.get("message", "")
                                    if message_piece and message_piece != "[结束]":
                                        ai_full_response += message_piece
                            except:
                                continue

        except Exception as e:
            print(f"[错误] 对话流处理失败：", e)
        finally:
            if ai_full_response:
                ai_full_response_cleaned = re.sub(
                    r"\{img\}.*?$", "", ai_full_response
                ).strip()
                conversation_history.append({"role": "user", "content": text})
                conversation_history.append(
                    {"role": "assistant", "content": ai_full_response_cleaned}
                )
                conversation_history = conversation_history[-CONTEXT_WINDOW_SIZE:]
                print(
                    f"[短期记忆] 更新完成，当前包含 {len(conversation_history)} 条消息。"
                )
            yield f"data: {json.dumps({'file': None, 'message': '[结束]', 'done': True})}\n\n"

    return StreamingResponse(audio_stream(), media_type="text/event-stream")
