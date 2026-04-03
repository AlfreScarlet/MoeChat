# 助手管理接口文档

本文档描述 MoeChat 的助手（Assistant）管理相关 API 端点。助手管理接口提供助手的增删改查、切换、资源文件管理等功能，所有接口均为标准 HTTP REST 端点，返回 JSON 格式响应。

---

## 端点概览

| 端点 | 方法 | 说明 |
|---|---|---|
| `/assistants` | GET | 获取所有助手列表 |
| `/assistant/current` | GET | 获取当前选中的助手信息 |
| `/assistant/switch` | POST | 切换当前使用的助手 |
| `/assistant/assets/check` | POST | 检查助手资源文件是否有更新 |
| `/assistant/assets/download` | POST | 下载助手资源文件（zip 包） |
| `/assistant/assets/upload` | POST | 上传助手资源文件（zip 包） |
| `/assistant/info/update` | POST | 更新助手信息 |
| `/assistant/info/add` | POST | 添加新助手 |
| `/assistant/info/delete` | POST | 删除助手 |

---

## GET /assistants

**描述**: 获取系统中所有已注册助手的信息列表。

**请求**:
- 方法: `GET`
- 参数: 无

**响应**:
- Content-Type: `application/json`
- 状态码: `200 OK`

**响应体格式**:

| 字段 | 类型 | 描述 |
|---|---|---|
| `msg` | string | 操作结果描述 |
| `data` | array | 助手信息对象列表 |
| `count` | integer | 助手总数 |

**示例**:

```bash
curl "http://localhost:8001/assistants"
```

响应（存在助手时）：

```json
{
  "msg": "Load assistants success",
  "data": [
    {
      "name": "Chat酱",
      "avatar": "avatar.png",
      "birthday": "1月1日",
      "personality": "活泼开朗",
      "description": "一个可爱的AI助手"
    }
  ],
  "count": 1
}
```

响应（无助手时）：

```json
{
  "msg": "No assistants found",
  "data": [],
  "count": 0
}
```

**错误处理**:

该端点无请求参数，一般不会产生客户端错误。

| 状态码 | 场景 | 说明 |
|---|---|---|
| 500 | 服务端加载助手信息失败 | 返回内部错误 |

---

## GET /assistant/current

**描述**: 获取当前选中的助手的详细信息。如果当前没有选中任何助手，返回 `null`。

**请求**:
- 方法: `GET`
- 参数: 无

**响应**:
- Content-Type: `application/json`
- 状态码: `200 OK`

**响应体格式**:

| 字段 | 类型 | 描述 |
|---|---|---|
| `msg` | string | 操作结果描述 |
| `data` | object \| null | 当前助手信息对象，未选中时为 `null` |

**示例**:

```bash
curl "http://localhost:8001/assistant/current"
```

响应（已选中助手时）：

```json
{
  "msg": "Get current assistant success",
  "data": {
    "name": "Chat酱",
    "avatar": "avatar.png",
    "birthday": "1月1日",
    "personality": "活泼开朗",
    "description": "一个可爱的AI助手"
  }
}
```

响应（未选中助手时）：

```json
{
  "msg": "No current assistant selected",
  "data": null
}
```

响应（助手信息未找到时）：

```json
{
  "msg": "Current assistant info not found",
  "data": null
}
```

**错误处理**:

| 状态码 | 场景 | 说明 |
|---|---|---|
| 500 | 获取当前助手信息时发生内部错误 | `{"detail": "获取当前助手信息失败: <错误信息>"}` |

---

## POST /assistant/switch

**描述**: 切换当前使用的助手。切换成功后会保存最后使用的助手信息，以便下次启动时自动加载。

**请求**:
- 方法: `POST`
- Content-Type: `application/json`

**请求体** (`SwitchAssistantRequest` 模型):

| 字段 | 类型 | 必填 | 描述 |
|---|---|---|---|
| `name` | string | 是 | 要切换到的助手名称 |

**请求体示例**:

```json
{
  "name": "Chat酱"
}
```

**响应**:
- Content-Type: `application/json`
- 状态码: `200 OK`

**响应体格式**:

| 字段 | 类型 | 描述 |
|---|---|---|
| `msg` | string | 操作结果描述 |
| `data` | object | 切换后的助手信息对象 |

**示例**:

```bash
curl -X POST "http://localhost:8001/assistant/switch" \
  -H "Content-Type: application/json" \
  -d '{"name": "Chat酱"}'
```

响应：

```json
{
  "msg": "成功切换到助手 'Chat酱'",
  "data": {
    "name": "Chat酱",
    "avatar": "avatar.png",
    "birthday": "1月1日",
    "personality": "活泼开朗",
    "description": "一个可爱的AI助手"
  }
}
```

**错误处理**:

| 状态码 | 场景 | 说明 |
|---|---|---|
| 404 | 指定名称的助手不存在 | `{"detail": "Assistant 'xxx' not found"}` |
| 422 | 请求体缺失或 `name` 字段缺失 | 返回验证错误 |
| 500 | 切换助手时发生内部错误 | `{"detail": "切换助手失败: <错误信息>"}` |

422 错误响应示例：

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json
```

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "name"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```


---

## POST /assistant/assets/check

**描述**: 检查指定助手的资源文件（assets 目录）是否有更新。客户端传入上次获取资源时的修改时间戳，服务端比较后返回是否需要重新下载。

**请求**:
- 方法: `POST`
- Content-Type: `application/json`

**请求体** (`AssistantAssetsCheckRequest` 模型):

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|---|---|---|---|---|
| `name` | string | 是 | - | 助手名称 |
| `lastModified` | float | 否 | `0` | 客户端保存的最后修改时间戳 |

**请求体示例**:

```json
{
  "name": "Chat酱",
  "lastModified": 1700000000.0
}
```

**响应**:
- Content-Type: `application/json`
- 状态码: `200 OK`

**响应体格式**:

| 字段 | 类型 | 描述 |
|---|---|---|
| `msg` | string | 操作结果描述 |
| `needsUpdate` | boolean | 是否需要更新资源 |
| `assetsLastModified` | float | 服务端资源的最新修改时间戳 |

**示例**:

```bash
curl -X POST "http://localhost:8001/assistant/assets/check" \
  -H "Content-Type: application/json" \
  -d '{"name": "Chat酱", "lastModified": 1700000000.0}'
```

响应（需要更新时）：

```json
{
  "msg": "Check update success",
  "needsUpdate": true,
  "assetsLastModified": 1700100000.0
}
```

响应（不需要更新时）：

```json
{
  "msg": "Check update success",
  "needsUpdate": false,
  "assetsLastModified": 1700000000.0
}
```

响应（assets 目录不存在时）：

```json
{
  "msg": "Assets directory not found",
  "needsUpdate": false,
  "assetsLastModified": 0
}
```

**错误处理**:

| 状态码 | 场景 | 说明 |
|---|---|---|
| 404 | 指定名称的助手不存在 | `{"detail": "Assistant 'xxx' not found"}` |
| 422 | 请求体缺失或 `name` 字段缺失 | 返回验证错误 |

422 错误响应示例：

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json
```

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "name"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

---

## POST /assistant/assets/download

**描述**: 下载指定助手的资源文件。服务端将助手的 `assets` 目录打包为 zip 文件返回。

**请求**:
- 方法: `POST`
- Content-Type: `application/json`

**请求体** (`AssistantAssetsDownloadRequest` 模型):

| 字段 | 类型 | 必填 | 描述 |
|---|---|---|---|
| `name` | string | 是 | 助手名称 |

**请求体示例**:

```json
{
  "name": "Chat酱"
}
```

**响应**:
- Content-Type: `application/zip`
- 状态码: `200 OK`
- Content-Disposition: `attachment; filename=assets.zip`

响应体为 zip 格式的二进制数据，包含助手 `assets` 目录下的所有文件，保持原始目录结构。

**示例**:

```bash
curl -X POST "http://localhost:8001/assistant/assets/download" \
  -H "Content-Type: application/json" \
  -d '{"name": "Chat酱"}' \
  --output assets.zip
```

**错误处理**:

| 状态码 | 场景 | 说明 |
|---|---|---|
| 404 | 指定名称的助手不存在 | `{"detail": "Assistant 'xxx' not found"}` |
| 404 | 助手的 assets 目录不存在 | `{"detail": "Assets directory not found for assistant 'xxx'"}` |
| 404 | 助手的 assets 目录为空 | `{"detail": "Assets is empty for assistant 'xxx'"}` |
| 422 | 请求体缺失或 `name` 字段缺失 | 返回验证错误 |

422 错误响应示例：

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json
```

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "name"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

---

## POST /assistant/assets/upload

**描述**: 上传助手的资源文件。接收一个包含 `assets` 目录内容的 zip 文件，解压后覆盖助手原有的 `assets` 目录。使用 `multipart/form-data` 格式提交。

**请求**:
- 方法: `POST`
- Content-Type: `multipart/form-data`

**请求参数**:

| 字段 | 类型 | 位置 | 必填 | 描述 |
|---|---|---|---|---|
| `name` | string | form | 是 | 助手名称（仅允许字母、数字、下划线和中文字符） |
| `assets_zip` | file | form | 是 | 包含资源文件的 zip 压缩包 |

> **注意**: zip 文件中可以包含 `assets/` 前缀目录，也可以直接包含文件。服务端会自动识别并正确解压。

**示例**:

```bash
curl -X POST "http://localhost:8001/assistant/assets/upload" \
  -F "name=Chat酱" \
  -F "assets_zip=@assets.zip"
```

**响应**:
- Content-Type: `application/json`
- 状态码: `200 OK`

**响应体格式**:

| 字段 | 类型 | 描述 |
|---|---|---|
| `status` | string | 操作状态，成功时为 `"success"` |
| `message` | string | 操作结果描述 |

响应示例：

```json
{
  "status": "success",
  "message": "Assets uploaded successfully for assistant 'Chat酱'"
}
```

**错误处理**:

| 状态码 | 场景 | 说明 |
|---|---|---|
| 400 | 助手名称格式无效（包含非法字符） | `{"detail": "Invalid assistant name format"}` |
| 400 | 助手名称包含路径遍历字符 | `{"detail": "Invalid assistant name"}` |
| 400 | 上传的文件不是有效的 zip 文件 | `{"detail": "Uploaded file is not a valid zip file"}` 或 `{"detail": "Invalid zip file format"}` |
| 404 | 指定名称的助手不存在 | `{"detail": "Assistant 'xxx' not found"}` |
| 422 | `name` 或 `assets_zip` 字段缺失 | 返回验证错误 |
| 500 | 解压或写入文件时发生内部错误 | `{"detail": "Failed to upload assets: <错误信息>"}` |

422 错误响应示例：

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json
```

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "name"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```


---

## POST /assistant/info/update

**描述**: 更新指定助手的信息。仅需传入 `name`（用于定位助手）和需要更新的字段，未传入的字段保持不变。

**请求**:
- 方法: `POST`
- Content-Type: `application/json`

**请求体** (`UpdateAssistantRequest` 模型):

| 字段 | 类型 | 必填 | 描述 |
|---|---|---|---|
| `name` | string | 是 | 助手名称（用于定位要更新的助手） |
| `avatar` | string \| null | 否 | 助手头像 |
| `birthday` | string \| null | 否 | 助手生日 |
| `height` | integer \| string \| null | 否 | 助手身高 |
| `weight` | integer \| string \| null | 否 | 助手体重 |
| `personality` | string \| null | 否 | 助手性格描述 |
| `description` | string \| null | 否 | 助手描述 |
| `user` | string \| null | 否 | 对用户的称呼 |
| `mask` | string \| null | 否 | 用户的设定 |
| `messageExamples` | array[string] \| null | 否 | 助手对话案例列表 |
| `extraDescription` | string \| null | 否 | 助手额外描述 |
| `customPrompt` | string \| null | 否 | 自定义提示词 |
| `startWith` | array[string] \| null | 否 | 助手开场白列表 |
| `settings` | object \| null | 否 | 助手设置（键值对） |
| `gsvSetting` | object \| null | 否 | 助手 GSV（GPT-SoVITS）语音设置 |

**请求体示例**（仅更新部分字段）:

```json
{
  "name": "Chat酱",
  "personality": "温柔体贴",
  "description": "一个温柔的AI助手",
  "startWith": ["你好呀~", "今天过得怎么样？"]
}
```

**响应**:
- Content-Type: `application/json`
- 状态码: `200 OK`

**响应体格式**:

| 字段 | 类型 | 描述 |
|---|---|---|
| `msg` | string | 操作结果描述 |
| `data` | object | 更新后的完整助手信息对象 |

响应示例：

```json
{
  "msg": "助手 'Chat酱' 信息更新成功",
  "data": {
    "name": "Chat酱",
    "avatar": "avatar.png",
    "birthday": "1月1日",
    "personality": "温柔体贴",
    "description": "一个温柔的AI助手",
    "user": "阁下",
    "mask": "",
    "messageExamples": [],
    "extraDescription": "",
    "customPrompt": "",
    "startWith": ["你好呀~", "今天过得怎么样？"],
    "settings": {},
    "gsvSetting": {}
  }
}
```

**错误处理**:

| 状态码 | 场景 | 说明 |
|---|---|---|
| 404 | 指定名称的助手不存在 | `{"detail": "<错误信息>"}` |
| 422 | 请求体缺失或 `name` 字段缺失 | 返回验证错误 |
| 500 | 更新助手信息时发生内部错误 | `{"detail": "更新助手信息失败: <错误信息>"}` |

422 错误响应示例：

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json
```

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "name"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

---

## POST /assistant/info/add

**描述**: 添加一个新的助手。需要提供助手的基本信息，部分字段有默认值。

**请求**:
- 方法: `POST`
- Content-Type: `application/json`

**请求体** (`AddAssistantRequest` 模型):

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|---|---|---|---|---|
| `name` | string | 是 | - | 助手名称 |
| `avatar` | string | 是 | - | 助手头像 |
| `birthday` | string | 是 | - | 助手生日 |
| `height` | integer \| string | 是 | - | 助手身高 |
| `weight` | integer \| string | 是 | - | 助手体重 |
| `personality` | string | 是 | - | 助手性格描述 |
| `description` | string | 是 | - | 助手描述 |
| `user` | string | 否 | `"阁下"` | 对用户的称呼 |
| `mask` | string | 否 | `""` | 用户的设定 |
| `messageExamples` | array[string] | 否 | `[]` | 助手对话案例列表 |
| `extraDescription` | string | 否 | `""` | 助手额外描述 |
| `customPrompt` | string | 否 | `""` | 自定义提示词 |
| `startWith` | array[string] | 否 | `[]` | 助手开场白列表 |
| `settings` | object | 否 | `{}` | 助手设置（键值对） |
| `gsvSetting` | object | 否 | `{}` | 助手 GSV（GPT-SoVITS）语音设置 |

**请求体示例**（仅必填字段）:

```json
{
  "name": "小雪",
  "avatar": "xiaoxue.png",
  "birthday": "12月25日",
  "height": 165,
  "weight": "48kg",
  "personality": "安静内敛，喜欢读书",
  "description": "一个文静的AI助手"
}
```

**请求体示例**（包含可选字段）:

```json
{
  "name": "小雪",
  "avatar": "xiaoxue.png",
  "birthday": "12月25日",
  "height": 165,
  "weight": "48kg",
  "personality": "安静内敛，喜欢读书",
  "description": "一个文静的AI助手",
  "user": "主人",
  "messageExamples": ["你好呀，主人~", "今天想聊些什么呢？"],
  "startWith": ["主人好~", "今天也要加油哦"],
  "settings": {
    "temperature": 0.7
  },
  "gsvSetting": {
    "refer_wav_path": "audio/ref.wav"
  }
}
```

**响应**:
- Content-Type: `application/json`
- 状态码: `200 OK`

**响应体格式**:

| 字段 | 类型 | 描述 |
|---|---|---|
| `msg` | string | 操作结果描述 |
| `data` | object | 新添加的助手信息对象 |

响应示例：

```json
{
  "msg": "助手 '小雪' 添加成功",
  "data": {
    "name": "小雪",
    "avatar": "xiaoxue.png",
    "birthday": "12月25日",
    "height": 165,
    "weight": "48kg",
    "personality": "安静内敛，喜欢读书",
    "description": "一个文静的AI助手",
    "user": "主人",
    "mask": "",
    "messageExamples": ["你好呀，主人~", "今天想聊些什么呢？"],
    "extraDescription": "",
    "customPrompt": "",
    "startWith": ["主人好~", "今天也要加油哦"],
    "settings": {"temperature": 0.7},
    "gsvSetting": {"refer_wav_path": "audio/ref.wav"}
  }
}
```

**错误处理**:

| 状态码 | 场景 | 说明 |
|---|---|---|
| 400 | 助手名称已存在或其他业务校验失败 | `{"detail": "<错误信息>"}` |
| 422 | 请求体缺失或必填字段缺失 | 返回验证错误 |
| 500 | 添加助手时发生内部错误 | `{"detail": "添加助手失败: <错误信息>"}` |

422 错误响应示例（缺失必填字段）：

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json
```

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "name"],
      "msg": "Field required",
      "input": null
    },
    {
      "type": "missing",
      "loc": ["body", "avatar"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

---

## POST /assistant/info/delete

**描述**: 删除指定的助手及其相关数据。

**请求**:
- 方法: `POST`
- Content-Type: `application/json`

**请求体** (`DeleteAssistantRequest` 模型):

| 字段 | 类型 | 必填 | 描述 |
|---|---|---|---|
| `name` | string | 是 | 要删除的助手名称 |

**请求体示例**:

```json
{
  "name": "小雪"
}
```

**响应**:
- Content-Type: `application/json`
- 状态码: `200 OK`

**响应体格式**:

| 字段 | 类型 | 描述 |
|---|---|---|
| `msg` | string | 操作结果描述 |

响应示例：

```json
{
  "msg": "助手 '小雪' 删除成功"
}
```

**错误处理**:

| 状态码 | 场景 | 说明 |
|---|---|---|
| 404 | 指定名称的助手不存在 | `{"detail": "<错误信息>"}` |
| 422 | 请求体缺失或 `name` 字段缺失 | 返回验证错误 |
| 500 | 删除助手时发生内部错误 | `{"detail": "删除助手失败: <错误信息>"}` |

422 错误响应示例：

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json
```

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "name"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```