import time
from pydantic import BaseModel, Field
import yaml


class GSVSetting(BaseModel):
    """
    助手语音合成设置模型
    """

    textLang: str = Field(..., description="助手语音合成的语言")
    gptModelPath: str = Field(..., description="助手语音合成的GPT模型")
    sovitsModelPath: str = Field(..., description="助手语音合成的SOVITS模型")
    refAudioPath: str = Field(..., description="助手语音合成的参考音频")
    promptText: str = Field(..., description="助手语音合成的参考文字")
    promptLang: str = Field(..., description="助手语音合成的参考文字语言")
    seed: int = Field(-1, description="助手语音合成的随机种子")
    topK: int = Field(30, description="助手语音合成的TopK")
    batchSize: int = Field(20, description="助手语音合成的批量大小")
    extra: dict = Field(
        {"text_split_method": "cut0"}, description="助手语音合成的额外参数"
    )
    extraRefAudio: dict = Field({}, description="助手语音合成的额外参考音频")

    @staticmethod
    def from_dict(data: dict) -> "GSVSetting":
        """
        从字典创建 GSVSetting 实例，如果有不存在的key则返回默认值
        """
        return GSVSetting(
            textLang=data.get("textLang", "zh"),
            gptModelPath=data.get("gptModelPath", ""),
            sovitsModelPath=data.get("sovitsModelPath", ""),
            refAudioPath=data.get("refAudioPath", ""),
            promptText=data.get("promptText", ""),
            promptLang=data.get("promptLang", "zh"),
            seed=data.get("seed", -1),
            topK=data.get("topK", 30),
            batchSize=data.get("batchSize", 20),
            extra=data.get("extra", {"text_split_method": "cut0"}),
            extraRefAudio=data.get("extraRefAudio", {}),
        )


class AssistantSettings(BaseModel):
    """
    助手设置模型
    """

    # 是否写入日记，单独控制是否写入助手的长期记忆数据；
    writeLongMemory: bool = Field(True, description="助手是否会写入日记")
    # 是否启用日记功能，日记功能可以长期储存对话信息，并根据用户输入的时间信息进行检索；比如：“昨天做了什么？”、“两天前吃的午饭是什么？
    enableLongMemory: bool = Field(True, description="助手是否开启日记功能")
    #  # 启用日记检索加强，使用嵌入模型对检索到的信息做提取，去除与用户提问不相关的内容。
    enableLongMemorySearchEnhance: bool = Field(
        True, description="助手是否开启日记功能的检索加强"
    )
    enableCoreMemory: bool = Field(True, description="助手是否开启核心记忆功能")
    # 日记内容搜索阈值，启用日志检索加强是需要，用于判断匹配程度。过高可能会丢失数据，过低则过滤少量无用记忆。
    longMemoryThreshold: float = Field(0.5, description="助手日记功能的搜索阈值")
    # 是否开启世界书(知识库)功能，开启后可以根据用户输入的问题，从知识库中检索相关内容。
    enableLoreBooks: bool = Field(True, description="助手是否开启世界书(知识库)功能")
    # 世界书(知识库)检索阈值，启用知识库功能是需要，用于判断匹配程度。过高可能会丢失数据，过低则过滤少量无用记忆。
    loreBooksThreshold: float = Field(
        0.5, description="助手世界书(知识库)功能的搜索阈值"
    )
    # 世界书搜索深度
    loreBooksDepth: int = Field(3, description="助手世界书(知识库)功能的搜索深度")
    # 是否启动情绪系统
    enableEmotionSystem: bool = Field(False, description="助手是否开启情绪系统")
    # 情绪值是否持续，设置为 true，重启后会读取上次的情绪值；false则每次重置为0
    enableEmotionPersist: bool = Field(
        False, description="助手是否开启情绪系统的持续存储"
    )
    # 情绪系统的上下文长度
    contextLength: int = Field(40, description="助手的上下文长度")

    @staticmethod
    def from_dict(data: dict) -> "AssistantSettings":
        """
        从字典创建 AssistantSettings 实例，如果有不存在的key则返回默认值
        """
        return AssistantSettings(
            writeLongMemory=data.get("writeLongMemory", True),
            enableLongMemory=data.get("enableLongMemory", True),
            enableLongMemorySearchEnhance=data.get(
                "enableLongMemorySearchEnhance", True
            ),
            enableCoreMemory=data.get("enableCoreMemory", True),
            longMemoryThreshold=data.get("longMemoryThreshold", 0.38),
            enableLoreBooks=data.get("enableLoreBooks", True),
            loreBooksThreshold=data.get("loreBooksThreshold", 0.5),
            loreBooksDepth=data.get("loreBooksDepth", 3),
            enableEmotionSystem=data.get("enableEmotionSystem", False),
            enableEmotionPersist=data.get("enableEmotionPersist", False),
            contextLength=data.get("contextLength", 40),
        )


class AssistantInfo(BaseModel):
    """
    助手信息模型
    """

    # 助手名称
    name: str = Field(..., description="助手名称")
    # 对用户的称呼
    user: str = Field(..., description="对用户的称呼")
    # 头像
    avatar: str = Field(..., description="助手头像")
    # 生日
    birthday: str = Field(..., description="助手生日")
    # 身高
    height: int | str = Field(..., description="助手身高")
    # 体重
    weight: int | str = Field(..., description="助手体重")
    # 角色性格
    personality: str = Field(..., description="助手性格")
    # 描述
    description: str = Field(..., description="助手描述")
    # 用户的设定，用于在提示词中填充用户的信息，进行个性化对话。
    mask: str = Field(..., description="用户的设定")
    # 初次相遇时间，存储为时间戳
    firstMeetTime: int = Field(..., description="助手初次相遇时间")
    # 好感度
    love: int = Field(..., description="助手好感度")
    # 对话案例
    messageExamples: list[str] = Field(..., description="助手对话案例")
    # 额外描述
    extraDescription: str = Field(..., description="助手额外描述")
    # 助手更新时间,存储为时间戳
    updatedAt: int = Field(..., description="助手更新时间")
    # 资产最后修改时间,存储为时间戳
    assetsLastModified: int = Field(..., description="助手资产最后修改时间")
    # 自定义提示词
    customPrompt: str = Field(..., description="自定义提示词")
    # 开场白，数组形式。用于创建开场内容，填入用户与AI的对话内容，只能填入用户和Ai的对话内容，开场白会直接被插入到上下文的开头。
    startWith: list[str] = Field(..., description="助手开场白")
    # 助手设置
    settings: AssistantSettings = Field(..., description="助手设置")
    # 助手GSV设置
    gsvSetting: GSVSetting = Field(..., description="助手GSV设置")

    emotionSetting: dict = Field({}, description="助手情绪系统设置")

    @staticmethod
    def from_dict(data: dict) -> "AssistantInfo":
        """
        从字典创建 AssistantInfo 实例，如果有不存在的key则返回默认值
        """
        return AssistantInfo(
            name=data.get("name", ""),
            user=data.get("user", "阁下"),
            avatar=data.get("avatar", ""),
            birthday=data.get("birthday", ""),
            height=data.get("height", ""),
            weight=data.get("weight", ""),
            personality=data.get("personality", ""),
            description=data.get("description", ""),
            mask=data.get("mask", ""),
            firstMeetTime=data.get("firstMeetTime", time.time()),
            love=data.get("love", 0),
            messageExamples=data.get("messageExamples", []),
            extraDescription=data.get("extraDescription", ""),
            updatedAt=data.get("updatedAt", time.time()),
            assetsLastModified=data.get("assetsLastModified", 0),
            settings=AssistantSettings.from_dict(data.get("settings", {})),
            customPrompt=data.get("customPrompt", ""),
            gsvSetting=GSVSetting.from_dict(data.get("gsvSetting", {})),
            startWith=data.get("startWith", []),
            emotionSetting=data.get("emotionSetting", {}),
        )


if __name__ == "__main__":
    # 测试数据
    test_data = {
        "name": "Chat酱",
        "user": "阁下",
        "avatar": "",
        "birthday": "2000-01-01",
        "height": "160",
        "weight": "50",
        "personality": "开朗",
        "description": "这是一个测试助手",
        "mask": "用户是一个18岁的男性",
        "firstMeetTime": 1620000000,
        "love": 50,
        "messageExamples": ["你好", "你好吗"],
        "extraDescription": "这是一个测试助手",
        "updatedAt": 1620000000,
        "assetsLastModified": 1620000000,
        "settings": {
            "enableLongMemory": True,
            "enableLongMemorySearchEnhance": True,
            "enableCoreMemory": True,
            "enableLoreBooks": True,
            "loreBooksThreshold": 0.5,
            "loreBooksDepth": 3,
            "enableEmotionSystem": False,
            "enableEmotionPersist": False,
            "contextLength": 40,
        },
        "customPrompt": "你是一个测试助手",
        "gsvSetting": {},
        "startWith": ["你好", "你好吗"],
    }
    # 创建 AssistantInfo 实例
    assistant_info = AssistantInfo.from_dict(test_data)
    # 打印实例属性
    print(assistant_info)
    with open("assistant_info.yaml", "w") as f:
        yaml.dump(
            assistant_info.model_dump(),
            stream=f,
            default_flow_style=False,
            allow_unicode=True,
            indent=4,
            sort_keys=False,
        )
