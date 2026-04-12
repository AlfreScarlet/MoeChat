from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class AssistantAssetsCheckRequest(BaseModel):
    """
    助手资源更新检查请求模型
    """

    name: str = Field(..., description="助手名称")
    lastModified: float = Field(0, description="客户端最后更新时间")


class AssistantAssetsDownloadRequest(BaseModel):
    """
    助手资源下载请求模型
    """

    name: str = Field(..., description="助手名称")


class UpdateAssistantRequest(BaseModel):
    """
    更新助手信息请求模型
    """

    name: str = Field(..., description="助手名称")
    avatar: Optional[str] = Field(None, description="助手头像")
    birthday: Optional[str] = Field(None, description="助手生日")
    height: Optional[int | str] = Field(None, description="助手身高")
    weight: Optional[int | str] = Field(None, description="助手体重")
    personality: Optional[str] = Field(None, description="助手性格")
    description: Optional[str] = Field(None, description="助手描述")
    user: Optional[str] = Field(None, description="对用户的称呼")
    mask: Optional[str] = Field(None, description="用户的设定")
    messageExamples: Optional[list[str]] = Field(None, description="助手对话案例")
    extraDescription: Optional[str] = Field(None, description="助手额外描述")
    customPrompt: Optional[str] = Field(None, description="自定义提示词")
    startWith: Optional[list[str]] = Field(None, description="助手开场白")
    settings: Optional[Dict[str, Any]] = Field(None, description="助手设置")
    gsvSetting: Optional[Dict[str, Any]] = Field(None, description="助手GSV设置")


class AddAssistantRequest(BaseModel):
    """
    添加助手信息请求模型
    """

    name: str = Field(..., description="助手名称")
    avatar: str = Field(..., description="助手头像")
    birthday: str = Field(..., description="助手生日")
    height: int | str = Field(..., description="助手身高")
    weight: int | str = Field(..., description="助手体重")
    personality: str = Field(..., description="助手性格")
    description: str = Field(..., description="助手描述")
    user: str = Field(default="阁下", description="对用户的称呼")
    mask: str = Field(default="", description="用户的设定")
    messageExamples: list[str] = Field(default_factory=list, description="助手对话案例")
    extraDescription: str = Field(default="", description="助手额外描述")
    customPrompt: str = Field(default="", description="自定义提示词")
    startWith: list[str] = Field(default_factory=list, description="助手开场白")
    settings: Dict[str, Any] = Field(default_factory=dict, description="助手设置")
    gsvSetting: Dict[str, Any] = Field(default_factory=dict, description="助手GSV设置")


class DeleteAssistantRequest(BaseModel):
    """
    删除助手信息请求模型
    """

    name: str = Field(..., description="助手名称")


# 切换助手请求模型
class SwitchAssistantRequest(BaseModel):
    name: str = Field(..., description="助手名称")

class GetAssistantAvatar(BaseModel):
    name: str = Field(..., description="助手名称")

class UploadAssistantAvatar(BaseModel):
    name: str = Field(..., description="助手名称")
    data: str = Field(..., description="头像数据，base64编码字符串")