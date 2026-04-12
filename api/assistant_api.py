import os
import re
import shutil
import zipfile
import io
import base64
from pathlib import Path
from models.dto.assistant_request import (
    AddAssistantRequest,
    AssistantAssetsCheckRequest,
    AssistantAssetsDownloadRequest,
    DeleteAssistantRequest,
    UpdateAssistantRequest,
    SwitchAssistantRequest,
    GetAssistantAvatar,
    UploadAssistantAvatar,
)

from services.assistant_service import AssistantService
from utils.file_utils import get_latest_modification_time
from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
)
from Config import Config
from utils.log import logger


assistant_api = APIRouter()

assistant_service = AssistantService()


@assistant_api.get("/assistants")
async def get_assistants():
    """
    获取所有助手信息

    Returns:
        包含所有助手信息的列表
    """
    assistants = assistant_service.load_assistant_info()

    if assistants:
        return {
            "msg": "Load assistants success",
            "data": assistants,
            "count": len(assistants),
        }
    else:
        return {"msg": "No assistants found", "data": assistants, "count": 0}


@assistant_api.get("/assistant/current")
async def get_current_assistant():
    """
    获取当前选择的助手信息

    Returns:
        当前助手的信息或空对象
    """
    try:
        # 获取当前助手名称
        current_assistant_name = assistant_service.get_current_assistant_name()

        if not current_assistant_name:
            return {"msg": "No current assistant selected", "data": None}

        # 获取当前助手的详细信息
        current_assistant = assistant_service.get_assistant_by_name(
            current_assistant_name
        )

        if current_assistant:
            return {
                "msg": "Get current assistant success",
                "data": current_assistant.model_dump(),
            }
        else:
            return {"msg": "Current assistant info not found", "data": None}
    except Exception as e:
        logger.error(f"获取当前助手信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取当前助手信息失败: {str(e)}")


@assistant_api.post("/assistant/switch")
async def switch_assistant(switch_request: SwitchAssistantRequest):
    """
    切换当前使用的助手

    Args:
        switch_request: 包含要切换的助手名称

    Returns:
        切换结果信息
    """
    try:
        # 调用服务层切换助手
        assistant_service.set_assistant(switch_request.name)

        # 保存最后使用的助手，以便下次启动时自动加载
        assistant_service.save_last_used_agent()

        # 获取助手详细信息返回给客户端
        assistant_info = assistant_service.get_assistant_by_name(switch_request.name)

        if not assistant_info:
            raise HTTPException(
                status_code=404,
                detail=f"Assistant '{switch_request.name}' not found",
            )

        return {
            "msg": f"成功切换到助手 '{switch_request.name}'",
            "data": assistant_info.model_dump(),
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"切换助手失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"切换助手失败: {str(e)}")


@assistant_api.post("/assistant/assets/check")
async def check_assets_update(
    assistant_assets_check: AssistantAssetsCheckRequest,
):
    """
    检查助手资源文件是否有更新

    Args:
        assistant_assets_check: 助手名称
        last_modified: 客户端保存的最后修改时间戳

    Returns:
        包含是否需要更新的信息
    """
    # 构建助手目录路径
    assistant_dir = os.path.join(Config.BASE_AGENTS_PATH, assistant_assets_check.name)
    assets_dir = os.path.join(assistant_dir, "assets")

    # 检查助手是否存在
    if not os.path.exists(assistant_dir):
        raise HTTPException(
            status_code=404,
            detail=f"Assistant '{assistant_assets_check.name}' not found",
        )

    # 检查assets目录是否存在
    if not os.path.exists(assets_dir):
        return {
            "msg": "Assets directory not found",
            "needsUpdate": False,
            "assetsLastModified": 0,
        }

    # 获取最新的修改时间
    latest_mtime = get_latest_modification_time(assets_dir)

    # 比较修改时间，判断是否需要更新
    needs_update = latest_mtime > assistant_assets_check.lastModified

    return {
        "msg": "Check update success",
        "needsUpdate": needs_update,
        "assetsLastModified": latest_mtime,
    }


@assistant_api.post("/assistant/assets/download")
async def download_assets(assistant_assets_download: AssistantAssetsDownloadRequest):
    """
    下载助手资源文件（assets目录），打包为zip文件

    Args:
        assistant_name: 助手名称

    Returns:
        zip格式的资源文件
    """
    # 构建助手目录路径
    assistant_dir = os.path.join(
        Config.BASE_AGENTS_PATH, assistant_assets_download.name
    )
    assets_dir = os.path.join(assistant_dir, "assets")

    # 检查助手是否存在
    if not os.path.exists(assistant_dir):
        raise HTTPException(
            status_code=404,
            detail=f"Assistant '{ assistant_assets_download.name}' not found",
        )

    # 检查assets目录是否存在
    if not os.path.exists(assets_dir):
        raise HTTPException(
            status_code=404,
            detail=f"Assets directory not found for assistant '{ assistant_assets_download.name}'",
        )

    # 创建内存中的zip文件
    zip_buffer = io.BytesIO()

    # 遍历assets目录，添加文件到zip
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        assets_path = Path(assets_dir)
        # 检查目录是否为空
        if not any(assets_path.iterdir()):
            # 如果目录为空
            raise HTTPException(
                status_code=404,
                detail=f"Assets is empty for assistant '{ assistant_assets_download.name}'",
            )
        else:
            # 添加所有文件
            for root, _, files in os.walk(assets_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # 计算相对路径，保持目录结构
                    rel_path = os.path.relpath(file_path, os.path.dirname(assets_dir))
                    zip_file.write(file_path, rel_path)

    # 重置文件指针
    zip_buffer.seek(0)

    # 返回zip文件
    return Response(
        content=zip_buffer.read(),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=assets.zip"},
    )


@assistant_api.post("/assistant/assets/upload")
async def upload_assets(
    name: str = Form(...),
    assets_zip: UploadFile = File(...),
):
    """
    上传助手资源文件（assets目录），覆盖原文件

    Args:
        assistant_name: 助手名称
        assets_zip: 包含assets目录的zip文件

    Returns:
        上传成功的消息
    """
    # 验证助手名称合法性
    if not name or not re.match(r"^[a-zA-Z0-9_\u4e00-\u9fa5]+$", name):
        raise HTTPException(status_code=400, detail="Invalid assistant name format")

    # 防止路径遍历攻击
    safe_name = os.path.basename(name)
    if safe_name != name:
        raise HTTPException(status_code=400, detail="Invalid assistant name")
    # 构建助手目录路径
    assistant_dir = os.path.join(Config.BASE_AGENTS_PATH, safe_name)

    # 检查助手是否存在
    if not os.path.exists(assistant_dir):
        raise HTTPException(
            status_code=404,
            detail=f"Assistant '{safe_name}' not found",
        )

    # 构建assets目录路径
    assets_dir = os.path.join(assistant_dir, "assets")

    # 读取上传的文件内容
    try:
        # 读取zip文件内容
        zip_content = await assets_zip.read()

        # 验证文件类型是否为zip
        if not zip_content.startswith(b"PK"):
            raise HTTPException(
                status_code=400, detail="Uploaded file is not a valid zip file"
            )

        # 如果原assets目录存在，先删除
        if os.path.exists(assets_dir):
            shutil.rmtree(assets_dir)

        # 创建新的assets目录
        os.makedirs(assets_dir, exist_ok=True)

        # 直接从zip文件中提取assets目录内容
        with zipfile.ZipFile(io.BytesIO(zip_content), "r") as zip_ref:
            # 获取zip文件中的所有文件列表
            zip_contents = zip_ref.namelist()

            # 检查是否包含assets目录
            has_assets_dir = any(item.startswith("assets/") for item in zip_contents)

            # 提取文件到目标目录
            for item in zip_contents:
                # 跳过目录项
                if item.endswith("/"):
                    continue

                if has_assets_dir:
                    # 如果zip中包含assets目录，需要去掉这个前缀
                    if item.startswith("assets/"):
                        # 去掉assets/前缀，保留剩余路径
                        target_path = os.path.join(assets_dir, item[7:])
                        # 确保目标文件的目录存在
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        # 提取文件
                        with (
                            zip_ref.open(item) as source,
                            open(target_path, "wb") as target,
                        ):
                            target.write(source.read())
                else:
                    # 如果zip中不包含assets目录，直接提取到assets目录
                    target_path = os.path.join(assets_dir, item)
                    # 确保目标文件的目录存在
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    # 提取文件
                    with (
                        zip_ref.open(item) as source,
                        open(target_path, "wb") as target,
                    ):
                        target.write(source.read())

        logger.info(f"Successfully uploaded assets for assistant: {safe_name}")

        return {
            "status": "success",
            "message": f"Assets uploaded successfully for assistant '{safe_name}'",
        }

    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid zip file format")
    except Exception as e:
        logger.error(f"Error uploading assets for assistant {safe_name}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to upload assets: {str(e)}"
        )


@assistant_api.post("/assistant/info/update")
async def update_assistant(update_request: UpdateAssistantRequest):
    """
    更新助手信息接口
    """
    try:
        # 调用服务层更新助手信息
        updated_assistant = assistant_service.update_assistant_info(update_request)

        return {
            "msg": f"助手 '{update_request.name}' 信息更新成功",
            "data": updated_assistant.model_dump(),
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"更新助手信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新助手信息失败: {str(e)}")


@assistant_api.post("/assistant/info/add")
async def add_assistant(add_request: AddAssistantRequest):
    """
    添加新助手接口
    """
    try:
        # 调用服务层添加助手
        new_assistant = assistant_service.add_assistant(add_request)

        return {
            "msg": f"助手 '{add_request.name}' 添加成功",
            "data": new_assistant.model_dump(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"添加助手失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加助手失败: {str(e)}")


@assistant_api.post("/assistant/info/delete")
async def delete_assistant(delete_request: DeleteAssistantRequest):
    """
    删除助手接口
    """
    try:
        # 调用服务层删除助手
        assistant_service.delete_assistant(delete_request.name)
        return {"msg": f"助手 '{delete_request.name}' 删除成功"}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"删除助手失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除助手失败: {str(e)}")


@assistant_api.post("/assistant/info/avatar")
async def get_assistant_avatar(get_request: GetAssistantAvatar):
    try:
        avatar_bytes = b""
        with open(f"data/agents/{get_request.name}/avatar", "rb") as f:
            avatar_bytes = f.read()
        avatar_base64 = base64.b64encode(avatar_bytes).decode("utf-8")
        return {"msg": "获取助手头像成功", "data": avatar_base64}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取助手头像失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取助手头像失败: {str(e)}")
    
    
@assistant_api.post("/assistant/upload/avatar")
async def upload_assistant_avatar(data: UploadAssistantAvatar):
    try:
        avatar_data = base64.b64decode(data.data)
        avatar_path = f"data/agents/{data.name}/avatar"
        with open(avatar_path, "wb") as f:
            f.write(avatar_data)
        return {"msg": "上传助手头像成功"}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"上传助手头像失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传助手头像失败: {str(e)}")