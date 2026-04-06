# MoeChat 助手管理接口文档

## 基础信息

| 项目 | 值 |
|---|---|
| 协议 | HTTP REST |
| 基础路径 | `http://{host}:{port}` |
| 默认端口 | `8000` |
| 请求格式 | `application/json`（资源上传接口除外） |
| 响应格式 | `application/json`（资源下载接口除外） |

---

## 目录

- [数据结构](#数据结构)
  - [AssistantInfo（助手完整信息）](#assistantinfo助手完整信息)
  - [AssistantSettings（功能设置）](#assistantsettings功能设置)
  - [GSVSetting（TTS 语音合成配置）](#gsvsettingtts-语音合成配置)
- [接口列表](#接口列表)
  - [1. 获取所有助手 GET /assistants](#1-获取所有助手)
  - [2. 获取当前助手 GET /assistant/current](#2-获取当前助手)
  - [3. 切换助手 POST /assistant/switch](#3-切换助手)
  - [4. 新增助手 POST /assistant/info/add](#4-新增助手)
  - [5. 更新助手信息 POST /assistant/info/update](#5-更新助手信息)
  - [6. 删除助手 POST /assistant/info/delete](#6-删除助手)
  - [7. 检查资源更新 POST /assistant/assets/check](#7-检查资源更新)
  - [8. 下载资源包 POST /assistant/assets/download](#8-下载资源包)
  - [9. 上传资源包 POST /assistant/assets/upload](#9-上传资源包)
- [典型使用流程](#典型使用流程)

---

## 数据结构

### AssistantInfo（助手完整信息）

这是助手的核心数据模型，所有返回助手信息的接口均使用此结构。

```jsonc
{
  // ========================
  // 基础身份信息
  // ========================

  // 助手名称，全局唯一标识符。
  // 同时作为服务端存储目录名（data/agents/{name}/）。
  // 命名规则：仅允许字母、数字、下划线、中文字符。
  "name": "Chat酱",

  // 助手头像的资源路径。
  // 通常指向 assets 目录中的图片文件，客户端可据此路径从资源包中加载头像。
  "avatar": "assistants/Chat酱/assets/images/assistant_avatar_medium.png",

  // 助手生日，字符串格式，建议使用 "YYYY-MM-DD"。
  // 用于角色设定展示，不影响对话逻辑。
  "birthday": "2022-03-17",

  // 助手身高，支持整数或字符串（如 160 或 "160"）。
  // 用于角色设定展示，不影响对话逻辑。
  "height": "160",

  // 助手体重，支持整数或字符串（如 50 或 "50"）。
  // 用于角色设定展示，不影响对话逻辑。
  "weight": "50",

  // ========================
  // 角色设定（影响 System Prompt）
  // ========================

  // 角色性格描述。
  // 会被注入到 system prompt 的「性格特点」段落中，
  // 指导 LLM 以该性格特征进行回复。
  "personality": "表面清纯可爱，实则腹黑毒舌，内心聪明机智，对很多事情有自己独特的看法。同时也有温柔体贴的一面，会在主人疲惫时给予暖心的安慰。",

  // 角色详细设定/描述。
  // 会被注入到 system prompt 的「角色设定」段落中，
  // 包含角色的外貌、背景故事、行为习惯等完整人设。
  // 这是影响角色表现最核心的字段。
  "description": "Chat酱是存在于现代科技世界手机中的器灵，诞生于手机的智能系统...",

  // 助手对用户的称呼。
  // 在 system prompt 中所有出现 {{user}} 的位置都会被替换为此值。
  // 例如设为"主人"，则 prompt 中会出现"与主人对话"等表述。
  "user": "阁下",

  // 用户的设定/人设。
  // 会被注入到 system prompt 的「用户设定」段落中，
  // 用于让角色了解用户的身份信息，实现个性化对话。
  // 例如："用户是一个18岁的男性，喜欢编程"。
  // 为空字符串时不注入该段落。
  "mask": "",

  // 对话案例列表。
  // 会被注入到 system prompt 的「对话示例」段落中，
  // 用于强化角色的说话风格和文风。
  // 每个元素是一条示例台词，不需要标注角色名。
  "messageExamples": [
    "人类视网膜的感光细胞不需要这种自杀式加班，您先休息一下吧。"
  ],

  // 额外描述信息。
  // 补充性的角色描述，目前作为扩展字段预留。
  "extraDescription": "",

  // 自定义提示词。
  // 直接追加到 system prompt 的末尾，不经过任何模板处理。
  // 适合添加特殊的行为指令，如"使用口语的文字风格进行对话，不要太啰嗦。"
  "customPrompt": "使用口语的文字风格进行对话，不要太啰嗦。",

  // 开场白列表。
  // 仅在助手首次对话（历史记录为空）时生效。
  // 数组元素按顺序交替作为 user 和 assistant 消息插入上下文开头：
  //   索引 0 → user, 索引 1 → assistant, 索引 2 → user, ...
  // 用于预设一段初始对话场景。
  "startWith": [],

  // ========================
  // 服务端维护的只读字段
  // ========================

  // 初次创建时间，Unix 时间戳（秒）。
  // 在调用 add 接口时由服务端自动生成，不可通过 update 修改。
  "firstMeetTime": 1620000000,

  // 好感度数值。
  // 由服务端内部逻辑维护，客户端只读。
  "love": 50,

  // 助手信息最后更新时间，Unix 时间戳（秒）。
  // 每次调用 update 接口时由服务端自动刷新。
  "updatedAt": 1620000000,

  // assets 资源目录的最新文件修改时间，Unix 时间戳（秒）。
  // 由服务端扫描 assets 目录计算得出，用于客户端判断是否需要重新下载资源。
  // 无 assets 目录时为 0。
  "assetsLastModified": 1620000000,

  // 情绪系统扩展参数。
  // 由服务端情绪引擎维护，客户端只读。
  "emotionSetting": {},

  // ========================
  // 嵌套配置对象
  // ========================

  // 功能开关与参数配置，详见 AssistantSettings。
  "settings": {
    "enableLongMemory": true,
    "enableLongMemorySearchEnhance": true,
    "enableCoreMemory": true,
    "longMemoryThreshold": 0.32,
    "enableLoreBooks": true,
    "loreBooksThreshold": 0.5,
    "loreBooksDepth": 3,
    "enableEmotionSystem": false,
    "enableEmotionPersist": false,
    "contextLength": 40
  },

  // TTS 语音合成配置，详见 GSVSetting。
  "gsvSetting": {
    "textLang": "zh",
    "gptModelPath": "models/【萝莉】女仆_Ver-1.4-e15.ckpt",
    "sovitsModelPath": "models/【萝莉】女仆_Ver-1.4_e24_s504.pth",
    "refAudioPath": "models/tmp/020.wav",
    "promptText": "嗯，谢谢您的夸奖，主人可以喜欢就好。",
    "promptLang": "zh",
    "seed": -1,
    "topK": 30,
    "batchSize": 20,
    "extra": {
      "text_split_method": "cut0"
    },
    "extraRefAudio": {}
  }
}
```


### AssistantSettings（功能设置）

控制助手的记忆、知识库、情绪等子系统的开关和参数。

```jsonc
{
  // 是否开启长期记忆（日记功能）。
  // 开启后，系统会自动将对话内容提取为日记条目并持久化存储。
  // 用户可以通过时间相关的提问来检索历史对话，
  // 例如："昨天做了什么？"、"两天前吃的午饭是什么？"
  "enableLongMemory": true,

  // 是否开启长期记忆检索增强。
  // 开启后，使用嵌入模型对检索到的日记内容做二次提取，
  // 去除与用户当前提问不相关的内容，提高检索精度。
  // 仅在 enableLongMemory 为 true 时有意义。
  "enableLongMemorySearchEnhance": true,

  // 是否开启核心记忆功能。
  // 开启后，系统会自动从对话中提取用户的关键个人信息
  // （如年龄、爱好、习惯、约定等），存入核心记忆库。
  // 后续对话中会通过语义匹配召回相关记忆，让角色"记住"用户。
  "enableCoreMemory": true,

  // 长期记忆（日记）检索的相似度阈值，范围 0.0 ~ 1.0。
  // 值越低，召回的记忆越多但可能包含不相关内容；
  // 值越高，召回越精确但可能遗漏有用信息。
  // 建议范围：0.3 ~ 0.5。
  "longMemoryThreshold": 0.32,

  // 是否开启知识库（世界书/Lore Books）功能。
  // 开启后，系统会根据用户输入从知识库中检索相关条目，
  // 并将匹配内容注入到 prompt 中，让角色具备特定领域知识。
  // 知识库数据存储在 data/agents/{name}/data_base/ 目录下。
  "enableLoreBooks": true,

  // 知识库检索的相似度阈值，范围 0.0 ~ 1.0。
  // 含义同 longMemoryThreshold。
  "loreBooksThreshold": 0.5,

  // 知识库检索返回的最大条目数。
  // 控制每次对话中最多注入多少条知识库内容。
  // 值越大信息越丰富，但会占用更多 token。
  "loreBooksDepth": 3,

  // 是否开启情绪系统。
  // 开启后，角色会维护一个动态的情绪状态（效价/唤醒度模型），
  // 情绪状态会影响角色的回复风格和语气。
  // 情绪引擎会根据对话内容实时更新情绪值。
  "enableEmotionSystem": false,

  // 是否开启情绪值持久化。
  // 为 true 时，服务重启后会恢复上次的情绪状态；
  // 为 false 时，每次重启情绪值重置为初始状态。
  // 仅在 enableEmotionSystem 为 true 时有意义。
  "enableEmotionPersist": false,

  // 上下文保留的最大消息轮数。
  // 当对话历史超过此数量时，服务端会自动触发摘要压缩：
  // 将旧的对话内容总结为一段摘要文本，然后清空历史记录，
  // 摘要会作为上下文前缀注入后续对话。
  // 值越大保留的原始对话越多，但 token 消耗也越大。
  "contextLength": 40
}
```

### GSVSetting（TTS 语音合成配置）

配置 GPT-SoVITS 语音合成引擎的参数。每个助手可以拥有独立的语音模型和参考音频。

```jsonc
{
  // 合成文本的语言。
  // 可选值："zh"（中文）、"en"（英文）、"ja"（日文）等。
  // 需要与角色的对话语言一致。
  "textLang": "zh",

  // GPT-SoVITS 的 GPT 模型文件路径。
  // 相对于 GPT-SoVITS 服务的工作目录。
  // 决定了语音合成的基础音色和韵律。
  "gptModelPath": "models/【萝莉】女仆_Ver-1.4-e15.ckpt",

  // GPT-SoVITS 的 SoVITS 模型文件路径。
  // 相对于 GPT-SoVITS 服务的工作目录。
  // 与 gptModelPath 配合使用，共同决定最终音色。
  "sovitsModelPath": "models/【萝莉】女仆_Ver-1.4_e24_s504.pth",

  // 参考音频文件路径。
  // GPT-SoVITS 使用此音频作为音色参考（few-shot），
  // 合成的语音会模仿此音频的音色特征。
  "refAudioPath": "models/tmp/020.wav",

  // 参考音频对应的文字内容。
  // 必须与 refAudioPath 指向的音频内容完全一致，
  // GPT-SoVITS 需要此文本来对齐音频特征。
  "promptText": "嗯，谢谢您的夸奖，主人可以喜欢就好。",

  // 参考音频文字的语言。
  // 需要与 promptText 的实际语言一致。
  "promptLang": "zh",

  // 随机种子。
  // 设为 -1 表示每次合成使用随机种子（结果不完全一致）；
  // 设为固定正整数可复现相同的合成结果。
  "seed": -1,

  // Top-K 采样参数。
  // 控制语音合成时的采样多样性，值越大变化越多。
  "topK": 30,

  // 批量处理大小。
  // 控制 TTS 引擎一次处理的文本块数量，影响合成速度。
  // 值越大速度越快，但显存占用也越大。
  "batchSize": 20,

  // 额外参数，传递给 GPT-SoVITS API 的扩展配置。
  // text_split_method: 文本分割方式，
  //   "cut0" = 不切分, "cut1" = 按标点切分,
  //   "cut2" = 按50字切分, "cut3" = 按中文句号切分,
  //   "cut4" = 按英文句号切分, "cut5" = 按标点+50字混合切分
  "extra": {
    "text_split_method": "cut0"
  },

  // 额外参考音频映射。
  // 用于多情绪音色切换场景，可配置不同情绪对应不同的参考音频。
  // 格式为 { "情绪名": { "refAudioPath": "...", "promptText": "...", "promptLang": "..." } }
  "extraRefAudio": {}
}
```

---

## 接口列表

### 1. 获取所有助手

```
GET /assistants
```

获取服务端 `data/agents/` 目录下所有已创建的助手信息列表。

#### 请求参数

无。

#### 响应示例

```jsonc
{
  "msg": "Load assistants success",
  // 助手总数
  "count": 1,
  // 助手信息数组，每个元素为完整的 AssistantInfo 对象
  "data": [
    {
      "name": "Chat酱",
      "avatar": "assistants/Chat酱/assets/images/assistant_avatar_medium.png",
      "birthday": "2022-03-17",
      "height": "160",
      "weight": "50",
      "personality": "表面清纯可爱，实则腹黑毒舌，内心聪明机智，对很多事情有自己独特的看法。同时也有温柔体贴的一面，会在主人疲惫时给予暖心的安慰。",
      "description": "Chat酱是存在于现代科技世界手机中的器灵，诞生于手机的智能系统...",
      "user": "阁下",
      "mask": "",
      "firstMeetTime": 1620000000,
      "love": 50,
      "messageExamples": [
        "人类视网膜的感光细胞不需要这种自杀式加班，您先休息一下吧。"
      ],
      "extraDescription": "",
      "updatedAt": 1620000000,
      "assetsLastModified": 1620000000,
      "customPrompt": "使用口语的文字风格进行对话，不要太啰嗦。",
      "startWith": [],
      "settings": {
        "enableLongMemory": true,
        "enableLongMemorySearchEnhance": true,
        "enableCoreMemory": true,
        "longMemoryThreshold": 0.32,
        "enableLoreBooks": true,
        "loreBooksThreshold": 0.5,
        "loreBooksDepth": 3,
        "enableEmotionSystem": false,
        "enableEmotionPersist": false,
        "contextLength": 40
      },
      "gsvSetting": {
        "textLang": "zh",
        "gptModelPath": "models/【萝莉】女仆_Ver-1.4-e15.ckpt",
        "sovitsModelPath": "models/【萝莉】女仆_Ver-1.4_e24_s504.pth",
        "refAudioPath": "models/tmp/020.wav",
        "promptText": "嗯，谢谢您的夸奖，主人可以喜欢就好。",
        "promptLang": "zh",
        "seed": -1,
        "topK": 30,
        "batchSize": 20,
        "extra": {
          "text_split_method": "cut0"
        },
        "extraRefAudio": {}
      },
      "emotionSetting": {}
    }
  ]
}
```

无助手时：

```jsonc
{
  "msg": "No assistants found",
  "count": 0,
  "data": []
}
```

---

### 2. 获取当前助手

```
GET /assistant/current
```

获取服务端当前激活（正在使用）的助手信息。服务端启动时会自动加载上次使用的助手，若无记录则尝试加载默认助手"Chat酱"。

#### 请求参数

无。

#### 响应示例（已选择助手）

```jsonc
{
  "msg": "Get current assistant success",
  // 完整的 AssistantInfo 对象
  "data": {
    "name": "Chat酱",
    "avatar": "assistants/Chat酱/assets/images/assistant_avatar_medium.png",
    "birthday": "2022-03-17",
    "height": "160",
    "weight": "50",
    "personality": "表面清纯可爱，实则腹黑毒舌，内心聪明机智，对很多事情有自己独特的看法。同时也有温柔体贴的一面，会在主人疲惫时给予暖心的安慰。",
    "description": "Chat酱是存在于现代科技世界手机中的器灵，诞生于手机的智能系统...",
    "user": "阁下",
    "mask": "",
    "firstMeetTime": 1620000000,
    "love": 50,
    "messageExamples": [
      "人类视网膜的感光细胞不需要这种自杀式加班，您先休息一下吧。"
    ],
    "extraDescription": "",
    "updatedAt": 1620000000,
    "assetsLastModified": 1620000000,
    "customPrompt": "使用口语的文字风格进行对话，不要太啰嗦。",
    "startWith": [],
    "settings": {
      "enableLongMemory": true,
      "enableLongMemorySearchEnhance": true,
      "enableCoreMemory": true,
      "longMemoryThreshold": 0.32,
      "enableLoreBooks": true,
      "loreBooksThreshold": 0.5,
      "loreBooksDepth": 3,
      "enableEmotionSystem": false,
      "enableEmotionPersist": false,
      "contextLength": 40
    },
    "gsvSetting": {
      "textLang": "zh",
      "gptModelPath": "models/【萝莉】女仆_Ver-1.4-e15.ckpt",
      "sovitsModelPath": "models/【萝莉】女仆_Ver-1.4_e24_s504.pth",
      "refAudioPath": "models/tmp/020.wav",
      "promptText": "嗯，谢谢您的夸奖，主人可以喜欢就好。",
      "promptLang": "zh",
      "seed": -1,
      "topK": 30,
      "batchSize": 20,
      "extra": {
        "text_split_method": "cut0"
      },
      "extraRefAudio": {}
    },
    "emotionSetting": {}
  }
}
```

#### 响应示例（未选择助手）

```jsonc
{
  "msg": "No current assistant selected",
  "data": null
}
```

#### 错误码

| 状态码 | 说明 |
|---|---|
| `500` | 服务端内部错误 |

---

### 3. 切换助手

```
POST /assistant/switch
```

切换服务端当前激活的助手。切换后服务端会加载该助手的 Agent 实例（包括记忆引擎、知识库、情绪引擎等），并记录为"上次使用的助手"以便下次启动自动加载。

已加载过的助手会复用 Agent 实例，无需重新初始化。

#### 请求体

```jsonc
{
  // [必填] 要切换到的助手名称，必须是已存在的助手
  "name": "Chat酱"
}
```

#### 响应示例

```jsonc
{
  "msg": "成功切换到助手 'Chat酱'",
  // 切换后的助手完整信息
  "data": {
    "name": "Chat酱",
    "avatar": "assistants/Chat酱/assets/images/assistant_avatar_medium.png",
    "birthday": "2022-03-17",
    "height": "160",
    "weight": "50",
    "personality": "表面清纯可爱，实则腹黑毒舌，内心聪明机智，对很多事情有自己独特的看法。同时也有温柔体贴的一面，会在主人疲惫时给予暖心的安慰。",
    "description": "Chat酱是存在于现代科技世界手机中的器灵，诞生于手机的智能系统...",
    "user": "阁下",
    "mask": "",
    "firstMeetTime": 1620000000,
    "love": 50,
    "messageExamples": [
      "人类视网膜的感光细胞不需要这种自杀式加班，您先休息一下吧。"
    ],
    "extraDescription": "",
    "updatedAt": 1620000000,
    "assetsLastModified": 1620000000,
    "customPrompt": "使用口语的文字风格进行对话，不要太啰嗦。",
    "startWith": [],
    "settings": {
      "enableLongMemory": true,
      "enableLongMemorySearchEnhance": true,
      "enableCoreMemory": true,
      "longMemoryThreshold": 0.32,
      "enableLoreBooks": true,
      "loreBooksThreshold": 0.5,
      "loreBooksDepth": 3,
      "enableEmotionSystem": false,
      "enableEmotionPersist": false,
      "contextLength": 40
    },
    "gsvSetting": {
      "textLang": "zh",
      "gptModelPath": "models/【萝莉】女仆_Ver-1.4-e15.ckpt",
      "sovitsModelPath": "models/【萝莉】女仆_Ver-1.4_e24_s504.pth",
      "refAudioPath": "models/tmp/020.wav",
      "promptText": "嗯，谢谢您的夸奖，主人可以喜欢就好。",
      "promptLang": "zh",
      "seed": -1,
      "topK": 30,
      "batchSize": 20,
      "extra": {
        "text_split_method": "cut0"
      },
      "extraRefAudio": {}
    },
    "emotionSetting": {}
  }
}
```

#### 错误码

| 状态码 | 说明 |
|---|---|
| `404` | 助手不存在或加载失败 |
| `500` | 服务端内部错误 |

---

### 4. 新增助手

```
POST /assistant/info/add
```

创建一个新的助手。服务端会自动创建目录结构 `data/agents/{name}/`，包含 `assets/`（资源文件）、`memory/`（长期记忆）、`data_base/`（知识库）三个子目录，并自动填充 `firstMeetTime`、`love`、`updatedAt`、`assetsLastModified` 等只读字段。

#### 请求体

```jsonc
{
  // [必填] 助手名称，全局唯一。
  // 命名规则：仅允许字母、数字、下划线、中文字符。
  // 不可与已有助手重名。
  "name": "新助手",

  // [必填] 头像资源路径
  "avatar": "assets/images/avatar.png",

  // [必填] 生日
  "birthday": "2000-01-01",

  // [必填] 身高
  "height": 160,

  // [必填] 体重
  "weight": 50,

  // [必填] 性格描述，注入 system prompt
  "personality": "温柔体贴，善解人意",

  // [必填] 角色详细设定，注入 system prompt。
  // 这是角色人设的核心内容，建议详细填写。
  "description": "你是一个温柔的助手，名叫新助手...",

  // [选填] 助手对用户的称呼，默认 "阁下"。
  // 在 prompt 模板中替换 {{user}} 占位符。
  "user": "主人",

  // [选填] 用户的人设，默认 ""。
  // 为空时不注入用户设定段落。
  "mask": "用户是一个20岁的大学生",

  // [选填] 对话案例列表，默认 []。
  // 用于强化角色文风。
  "messageExamples": [
    "今天天气真好呢，主人要不要出去走走？",
    "主人辛苦了，要不要休息一下？"
  ],

  // [选填] 额外描述，默认 ""
  "extraDescription": "",

  // [选填] 自定义提示词，默认 ""。
  // 直接追加到 prompt 末尾。
  "customPrompt": "回复要简洁，不超过100字。",

  // [选填] 开场白列表，默认 []。
  // 按 user/assistant 交替插入上下文开头。
  "startWith": [
    "你好呀",
    "主人好！今天有什么我可以帮忙的吗？"
  ],

  // [选填] 功能设置，默认使用 AssistantSettings 各字段的默认值。
  // 可以只传入需要覆盖默认值的字段。
  "settings": {
    "enableLongMemory": true,
    "enableLongMemorySearchEnhance": true,
    "enableCoreMemory": true,
    "longMemoryThreshold": 0.38,
    "enableLoreBooks": true,
    "loreBooksThreshold": 0.5,
    "loreBooksDepth": 3,
    "enableEmotionSystem": false,
    "enableEmotionPersist": false,
    "contextLength": 40
  },

  // [选填] TTS 语音合成配置，默认使用 GSVSetting 各字段的默认值。
  // 如果不需要语音功能可传空对象 {}。
  "gsvSetting": {
    "textLang": "zh",
    "gptModelPath": "",
    "sovitsModelPath": "",
    "refAudioPath": "",
    "promptText": "",
    "promptLang": "zh",
    "seed": -1,
    "topK": 30,
    "batchSize": 20,
    "extra": {
      "text_split_method": "cut0"
    },
    "extraRefAudio": {}
  }
}
```

#### 响应示例

```jsonc
{
  "msg": "助手 '新助手' 添加成功",
  // 返回完整的 AssistantInfo，包含服务端自动生成的字段
  "data": {
    "name": "新助手",
    "avatar": "assets/images/avatar.png",
    "birthday": "2000-01-01",
    "height": 160,
    "weight": 50,
    "personality": "温柔体贴，善解人意",
    "description": "你是一个温柔的助手，名叫新助手...",
    "user": "主人",
    "mask": "用户是一个20岁的大学生",
    "firstMeetTime": 1712345678,       // 服务端自动生成的创建时间戳
    "love": 0,                          // 初始好感度为 0
    "messageExamples": [
      "今天天气真好呢，主人要不要出去走走？",
      "主人辛苦了，要不要休息一下？"
    ],
    "extraDescription": "",
    "updatedAt": 1712345678,            // 服务端自动生成，与 firstMeetTime 相同
    "assetsLastModified": 0,            // 新建助手无资源文件，为 0
    "customPrompt": "回复要简洁，不超过100字。",
    "startWith": [
      "你好呀",
      "主人好！今天有什么我可以帮忙的吗？"
    ],
    "settings": {
      "enableLongMemory": true,
      "enableLongMemorySearchEnhance": true,
      "enableCoreMemory": true,
      "longMemoryThreshold": 0.38,
      "enableLoreBooks": true,
      "loreBooksThreshold": 0.5,
      "loreBooksDepth": 3,
      "enableEmotionSystem": false,
      "enableEmotionPersist": false,
      "contextLength": 40
    },
    "gsvSetting": {
      "textLang": "zh",
      "gptModelPath": "",
      "sovitsModelPath": "",
      "refAudioPath": "",
      "promptText": "",
      "promptLang": "zh",
      "seed": -1,
      "topK": 30,
      "batchSize": 20,
      "extra": {
        "text_split_method": "cut0"
      },
      "extraRefAudio": {}
    },
    "emotionSetting": {}
  }
}
```

#### 错误码

| 状态码 | 说明 |
|---|---|
| `400` | 助手名称已存在、名称为空或格式非法 |
| `500` | 创建失败 |

---

### 5. 更新助手信息

```
POST /assistant/info/update
```

更新已有助手的配置信息。采用增量更新策略：只有请求体中明确传入的字段会被更新，未传入的字段保持原值不变。

如果更新的是当前正在使用的助手，服务端会自动重新加载 Agent 实例，使新配置立即生效（包括重新构建 prompt、重新加载记忆引擎等）。

#### 请求体

```jsonc
{
  // [必填] 要更新的助手名称，用于定位目标助手
  "name": "Chat酱",

  // 以下所有字段均为 [选填]，只传入需要修改的字段即可。
  // 未传入的字段不会被修改。

  "avatar": "assets/images/new_avatar.png",   // 更新头像
  "birthday": "2022-03-17",                    // 更新生日
  "height": 165,                               // 更新身高
  "weight": 48,                                // 更新体重
  "personality": "更新后的性格描述",             // 更新性格
  "description": "更新后的角色设定...",          // 更新角色设定
  "user": "主人",                               // 更新对用户的称呼
  "mask": "用户是一个程序员",                    // 更新用户设定
  "messageExamples": ["新的对话案例1"],          // 更新对话案例（整体替换）
  "extraDescription": "补充描述",               // 更新额外描述
  "customPrompt": "新的自定义提示词",            // 更新自定义提示词
  "startWith": ["你好", "你好呀！"],             // 更新开场白（整体替换）

  // 更新 settings 时，传入的对象会与原有 settings 合并。
  // 注意：这是浅合并（shallow merge），即 settings 对象整体替换。
  // 建议客户端先获取完整 settings，修改后整体传回。
  "settings": {
    "enableEmotionSystem": true,
    "contextLength": 60,
    "enableLongMemory": true,
    "enableLongMemorySearchEnhance": true,
    "enableCoreMemory": true,
    "longMemoryThreshold": 0.32,
    "enableLoreBooks": true,
    "loreBooksThreshold": 0.5,
    "loreBooksDepth": 3,
    "enableEmotionPersist": false
  },

  // 更新 gsvSetting 同理，建议整体传回。
  "gsvSetting": {
    "textLang": "zh",
    "gptModelPath": "models/new_model.ckpt",
    "sovitsModelPath": "models/new_model.pth",
    "refAudioPath": "models/tmp/new_ref.wav",
    "promptText": "新的参考文字",
    "promptLang": "zh",
    "seed": -1,
    "topK": 30,
    "batchSize": 20,
    "extra": {
      "text_split_method": "cut0"
    },
    "extraRefAudio": {}
  }
}
```

#### 最小请求示例

只修改性格和上下文长度：

```jsonc
{
  "name": "Chat酱",
  "personality": "活泼开朗，喜欢冒险",
  "settings": {
    "enableLongMemory": true,
    "enableLongMemorySearchEnhance": true,
    "enableCoreMemory": true,
    "longMemoryThreshold": 0.32,
    "enableLoreBooks": true,
    "loreBooksThreshold": 0.5,
    "loreBooksDepth": 3,
    "enableEmotionSystem": false,
    "enableEmotionPersist": false,
    "contextLength": 80
  }
}
```

#### 响应示例

```jsonc
{
  "msg": "助手 'Chat酱' 信息更新成功",
  // 返回更新后的完整 AssistantInfo
  "data": {
    "name": "Chat酱",
    "avatar": "assistants/Chat酱/assets/images/assistant_avatar_medium.png",
    "birthday": "2022-03-17",
    "height": "160",
    "weight": "50",
    "personality": "活泼开朗，喜欢冒险",    // 已更新
    "description": "Chat酱是存在于现代科技世界手机中的器灵，诞生于手机的智能系统...",  // 未传入，保持原值
    "user": "阁下",                          // 未传入，保持原值
    "mask": "",
    "firstMeetTime": 1620000000,             // 只读字段，不可修改
    "love": 50,                              // 只读字段，不可修改
    "messageExamples": [
      "人类视网膜的感光细胞不需要这种自杀式加班，您先休息一下吧。"
    ],
    "extraDescription": "",
    "updatedAt": 1712399999,                 // 服务端自动刷新为当前时间
    "assetsLastModified": 1620000000,        // 服务端重新扫描 assets 目录
    "customPrompt": "使用口语的文字风格进行对话，不要太啰嗦。",
    "startWith": [],
    "settings": {
      "enableLongMemory": true,
      "enableLongMemorySearchEnhance": true,
      "enableCoreMemory": true,
      "longMemoryThreshold": 0.32,
      "enableLoreBooks": true,
      "loreBooksThreshold": 0.5,
      "loreBooksDepth": 3,
      "enableEmotionSystem": false,
      "enableEmotionPersist": false,
      "contextLength": 80                    // 已更新
    },
    "gsvSetting": {
      "textLang": "zh",
      "gptModelPath": "models/【萝莉】女仆_Ver-1.4-e15.ckpt",
      "sovitsModelPath": "models/【萝莉】女仆_Ver-1.4_e24_s504.pth",
      "refAudioPath": "models/tmp/020.wav",
      "promptText": "嗯，谢谢您的夸奖，主人可以喜欢就好。",
      "promptLang": "zh",
      "seed": -1,
      "topK": 30,
      "batchSize": 20,
      "extra": {
        "text_split_method": "cut0"
      },
      "extraRefAudio": {}
    },
    "emotionSetting": {}
  }
}
```

#### 错误码

| 状态码 | 说明 |
|---|---|
| `404` | 助手不存在 |
| `500` | 更新失败 |

---

### 6. 删除助手

```
POST /assistant/info/delete
```

删除指定助手及其所有数据。此操作会删除 `data/agents/{name}/` 整个目录，包括配置文件、对话历史、记忆数据、知识库数据和资源文件，不可恢复。

如果删除的是当前正在使用的助手，服务端会释放该助手的 Agent 实例，当前助手状态变为空。

#### 请求体

```jsonc
{
  // [必填] 要删除的助手名称
  "name": "新助手"
}
```

#### 响应示例

```jsonc
{
  "msg": "助手 '新助手' 删除成功"
}
```

#### 错误码

| 状态码 | 说明 |
|---|---|
| `404` | 助手不存在 |
| `500` | 删除失败 |

---

### 7. 检查资源更新

```
POST /assistant/assets/check
```

检查指定助手的 assets 资源目录是否有更新。客户端应在本地缓存 `assetsLastModified` 时间戳，每次需要使用资源时先调用此接口比对，判断是否需要重新下载。

#### 请求体

```jsonc
{
  // [必填] 助手名称
  "name": "Chat酱",

  // [必填] 客户端本地缓存的上次下载时间戳。
  // 首次检查时传 0，后续传上次响应中的 assetsLastModified 值。
  "lastModified": 1712345678.0
}
```

#### 响应示例（需要更新）

```jsonc
{
  "msg": "Check update success",
  // 是否需要重新下载资源。
  // 判断逻辑：服务端 assets 目录最新修改时间 > 客户端传入的 lastModified
  "needsUpdate": true,
  // 服务端 assets 目录的最新文件修改时间戳。
  // 客户端应保存此值，下次检查时作为 lastModified 传入。
  "assetsLastModified": 1712399999.0
}
```

#### 响应示例（无需更新）

```jsonc
{
  "msg": "Check update success",
  "needsUpdate": false,
  "assetsLastModified": 1712345678.0
}
```

#### 响应示例（无 assets 目录）

```jsonc
{
  "msg": "Assets directory not found",
  "needsUpdate": false,
  "assetsLastModified": 0
}
```

#### 错误码

| 状态码 | 说明 |
|---|---|
| `404` | 助手不存在 |

---

### 8. 下载资源包

```
POST /assistant/assets/download
```

将指定助手的 `assets/` 目录打包为 zip 文件下载。zip 内保留 `assets/` 前缀的目录结构。

#### 请求体

```jsonc
{
  // [必填] 助手名称
  "name": "Chat酱"
}
```

#### 响应

成功时返回二进制 zip 文件流：

```
HTTP/1.1 200 OK
Content-Type: application/zip
Content-Disposition: attachment; filename=assets.zip

<zip 二进制数据>
```

zip 内部结构示例：

```
assets/
├── images/
│   ├── assistant_avatar_medium.png
│   └── background.jpg
├── audio/
│   └── greeting.wav
└── ...
```

#### 错误码

| 状态码 | 说明 |
|---|---|
| `404` | 助手不存在、assets 目录不存在或 assets 目录为空 |

---

### 9. 上传资源包

```
POST /assistant/assets/upload
Content-Type: multipart/form-data
```

上传 zip 格式的资源包，覆盖指定助手的 `assets/` 目录。上传后原有的 assets 目录会被完全删除并替换为新内容。

zip 文件内可以包含或不包含 `assets/` 前缀目录，服务端会自动识别并正确解压。

#### 请求表单字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `name` | string | 是 | 助手名称。仅允许字母、数字、下划线、中文字符。 |
| `assets_zip` | file | 是 | zip 格式的资源包文件 |

#### 请求示例（curl）

```bash
curl -X POST http://localhost:8000/assistant/assets/upload \
  -F "name=Chat酱" \
  -F "assets_zip=@./assets.zip"
```

#### 响应示例

```jsonc
{
  "status": "success",
  "message": "Assets uploaded successfully for assistant 'Chat酱'"
}
```

#### 错误码

| 状态码 | 说明 |
|---|---|
| `400` | 助手名称格式非法、文件不是有效的 zip 格式 |
| `404` | 助手不存在 |
| `500` | 上传处理失败 |

---

## 典型使用流程

### 客户端启动初始化

```
1. GET /assistants                    → 获取所有助手列表，渲染助手选择界面
2. GET /assistant/current             → 获取服务端当前激活的助手，同步客户端状态
3. POST /assistant/assets/check       → 检查当前助手的资源是否需要更新
4. POST /assistant/assets/download    → 如需更新则下载资源包，解压到本地缓存
```

### 切换助手

```
1. POST /assistant/switch             → 切换到目标助手（首次加载可能耗时较长）
2. POST /assistant/assets/check       → 检查新助手的资源是否已缓存
3. POST /assistant/assets/download    → 如需更新则下载
```

### 创建新助手

```
1. POST /assistant/info/add           → 创建助手（填写基础信息和配置）
2. POST /assistant/assets/upload      → 上传头像、立绘等资源文件
3. POST /assistant/switch             → 切换到新创建的助手开始对话
```

### 编辑助手配置

```
1. GET /assistant/current             → 获取当前助手完整信息
2. （客户端展示编辑界面，用户修改字段）
3. POST /assistant/info/update        → 提交修改（仅传入变更的字段）
```

### 资源同步

```
1. POST /assistant/assets/check       → 定期或切换助手时检查
   ├─ needsUpdate: true  → POST /assistant/assets/download → 下载并更新本地缓存
   └─ needsUpdate: false → 使用本地缓存
```
