# 聊天接口文档

本文档描述 MoeChat 的聊天相关 API 端点。所有聊天接口均返回 SSE（Server-Sent Events）流式响应，用于实时推送 LLM 生成的文本和 TTS 合成的音频数据。

---

## 端点概览

| 端点 | 方法 | 说明 |
|---|---|---|
| `/stream_chat` | GET | 简化版聊天接口，通过 query 参数发送单条文本 |
| `/chat` | POST | 标准聊天接口，支持多轮对话消息列表 |
| `/chat_v2` | POST | 增强版聊天接口，使用 `text_llm_tts_v2` 增强管线 |

---

## GET /stream_chat

**描述**: 简化版流式聊天接口。接收用户输入的单条文本，内部将其包装为 `[{"role": "user", "content": text}]` 消息列表后，调用与 `/chat` 相同的 LLM + TTS 管线，以 SSE 流式返回结果。

**请求**:
- 方法: `GET`
- Content-Type: 无（query 参数）

**参数**:

| 字段 | 类型 | 位置 | 必填 | 描述 |
|---|---|---|---|---|
| `text` | string | query | 是 | 用户输入的文本内容 |

**响应**:
- Content-Type: `text/event-stream`
- 状态码: `200 OK`

**SSE 数据帧格式**:

```
data: {"text": "你好", "audio": "base64..."}\n\n
data: {"text": "世界", "audio": "base64..."}\n\n
```

每个 SSE 帧包含一个 JSON 对象：

| 字段 | 类型 | 描述 |
|---|---|---|
| `text` | string | LLM 生成的文本片段 |
| `audio` | string | 对应文本片段的 TTS 音频数据（base64 编码） |

**示例**:

```bash
curl -N "http://localhost:8001/stream_chat?text=你好"
```

响应（SSE 流）：

```
data: {"text": "你好", "audio": "UklGRiQA..."}\n\n
data: {"text": "，有什么", "audio": "UklGRkBA..."}\n\n
data: {"text": "可以帮你的吗？", "audio": "UklGRlgA..."}\n\n
```


**错误处理**:

| 状态码 | 场景 | 说明 |
|---|---|---|
| 422 | `text` 参数缺失 | 返回验证错误 |

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
      "loc": ["query", "text"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

---

## POST /chat

**描述**: 标准流式聊天接口。接收包含多轮对话历史的消息列表，调用 LLM + TTS 管线（`text_llm_tts`），以 SSE 流式返回生成的文本和音频。

**请求**:
- 方法: `POST`
- Content-Type: `application/json`

**请求体** (`tts_data` 模型):

| 字段 | 类型 | 必填 | 描述 |
|---|---|---|---|
| `msg` | array | 是 | 消息列表，每项为一个消息对象 |

`msg` 数组中每个消息对象的格式：

| 字段 | 类型 | 必填 | 描述 |
|---|---|---|---|
| `role` | string | 是 | 消息角色，取值为 `"user"` 或 `"assistant"` |
| `content` | string | 是 | 消息内容 |

**请求体示例**:

```json
{
  "msg": [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好呀！有什么可以帮你的吗？"},
    {"role": "user", "content": "今天天气怎么样？"}
  ]
}
```

**响应**:
- Content-Type: `text/event-stream`
- 状态码: `200 OK`

**SSE 数据帧格式**:

```
data: {"text": "今天", "audio": "base64..."}\n\n
data: {"text": "天气不错呢！", "audio": "base64..."}\n\n
```

每个 SSE 帧包含一个 JSON 对象：

| 字段 | 类型 | 描述 |
|---|---|---|
| `text` | string | LLM 生成的文本片段 |
| `audio` | string | 对应文本片段的 TTS 音频数据（base64 编码） |

**示例**:

```bash
curl -N -X POST "http://localhost:8001/chat" \
  -H "Content-Type: application/json" \
  -d '{"msg": [{"role": "user", "content": "你好"}]}'
```

响应（SSE 流）：

```
data: {"text": "你好呀", "audio": "UklGRiQA..."}\n\n
data: {"text": "！今天过得怎么样？", "audio": "UklGRkBA..."}\n\n
```

**错误处理**:

| 状态码 | 场景 | 说明 |
|---|---|---|
| 422 | 请求体缺失或 `msg` 字段缺失 | 返回验证错误 |
| 422 | 请求体格式不是有效的 JSON | 返回验证错误 |

422 错误响应示例（缺失 `msg` 字段）：

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json
```

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "msg"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

---

## POST /chat_v2

**描述**: 增强版流式聊天接口。请求格式与 `/chat` 完全相同，区别在于内部调用 `text_llm_tts_v2` 增强版管线，支持更丰富的流式输出处理。

**与 `/chat` 的区别**:
- `/chat` 调用标准管线 `text_llm_tts`
- `/chat_v2` 调用增强管线 `text_llm_tts_v2`，在流式处理流程上进行了优化和增强

**请求**:
- 方法: `POST`
- Content-Type: `application/json`

**请求体** (`tts_data` 模型):

| 字段 | 类型 | 必填 | 描述 |
|---|---|---|---|
| `msg` | array | 是 | 消息列表，每项为一个消息对象 |

`msg` 数组中每个消息对象的格式：

| 字段 | 类型 | 必填 | 描述 |
|---|---|---|---|
| `role` | string | 是 | 消息角色，取值为 `"user"` 或 `"assistant"` |
| `content` | string | 是 | 消息内容 |

**响应**:
- Content-Type: `text/event-stream`
- 状态码: `200 OK`

**SSE 数据帧格式**:

```
data: {"text": "你好", "audio": "base64..."}\n\n
data: {"text": "世界", "audio": "base64..."}\n\n
```

每个 SSE 帧包含一个 JSON 对象：

| 字段 | 类型 | 描述 |
|---|---|---|
| `text` | string | LLM 生成的文本片段 |
| `audio` | string | 对应文本片段的 TTS 音频数据（base64 编码） |

**示例**:

```bash
curl -N -X POST "http://localhost:8001/chat_v2" \
  -H "Content-Type: application/json" \
  -d '{"msg": [{"role": "user", "content": "给我讲个故事吧"}]}'
```

响应（SSE 流）：

```
data: {"text": "从前", "audio": "UklGRiQA..."}\n\n
data: {"text": "有一座山，", "audio": "UklGRkBA..."}\n\n
data: {"text": "山里有一座庙...", "audio": "UklGRlgA..."}\n\n
```

**错误处理**:

| 状态码 | 场景 | 说明 |
|---|---|---|
| 422 | 请求体缺失或 `msg` 字段缺失 | 返回验证错误 |
| 422 | 请求体格式不是有效的 JSON | 返回验证错误 |

422 错误响应示例（请求体非 JSON 格式）：

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json
```

```json
{
  "detail": [
    {
      "type": "json_invalid",
      "loc": ["body", 0],
      "msg": "JSON decode error",
      "input": {}
    }
  ]
}
```
