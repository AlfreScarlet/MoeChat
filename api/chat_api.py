from fastapi.responses import StreamingResponse
from fastapi import APIRouter, HTTPException
from models.dto.tts_request import tts_data
import core.chat_core as chat_core
from fastapi import Query
from services.assistant_service import AssistantService

chat_api = APIRouter()
assistant_service = AssistantService()


@chat_api.get("/stream_chat")
async def tts_api_get_v1(text: str = Query(..., description="用户输入的文本")):

    message_list = [{"role": "user", "content": text}]

    params = tts_data(msg=message_list)

    return StreamingResponse(
        chat_core.text_llm_tts(params), media_type="text/event-stream"
    )


@chat_api.post("/chat")
async def tts_api_v1(params: tts_data):
    return StreamingResponse(
        chat_core.text_llm_tts(params), media_type="text/event-stream"
    )


@chat_api.post("/chat_v2")
async def tts_api_v2(params: tts_data):
    return StreamingResponse(
        chat_core.text_llm_tts_v2(params), media_type="text/event-stream"
    )


@chat_api.post("/chat/context/clear")
async def clear_chat_context():
    agent = assistant_service.get_current_assistant()
    if not agent:
        raise HTTPException(status_code=404, detail="No current assistant selected")
    try:
        agent.clear_chat_context()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear context: {e}")
    return {"msg": "Chat context cleared"}


# # 客户端获取聊天记录
# @chat_api.post("/get_context")
# async def get_context():
#     agent = Agent()
#     return agent.msg_data
