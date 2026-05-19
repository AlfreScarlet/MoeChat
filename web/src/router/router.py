from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from web.src.router.api_router import api_router
from web.src.controller.controller import templates

# Legacy experimental router. It contains HeWeather/image/meme branches, but the
# main web chat currently uses /api/stream_chat -> core.chat_core instead. Do not
# mount this router without a dedicated integration pass and end-to-end checks.
# from core.external_server import router as models_router

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 挂载各种路由
# app.include_router(models_router, prefix="/web")
app.include_router(templates)
app.include_router(api_router)
app.mount("/", StaticFiles(directory="web/resources/static", html=True), name="static")
