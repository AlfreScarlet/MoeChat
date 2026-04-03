# 语音识别（ASR）接口文档

本文档描述 MoeChat 的语音识别（Automatic Speech Recognition）相关 API 端点。包含一个 HTTP 端点用于单次识别，以及两个 WebSocket 端点用于实时流式识别。

---

## 端点概览

| 端点 | 方法 | 说明 |
|---|---|---|
| `/asr` | POST | 非流式语音识别，上传完整音频获取识别结果 |
| `/asr_ws` | WebSocket | 实时流式语音识别，仅返回识别文本 |
| `/asr_ws_plus` | WebSocket | 增强版实时流式语音识别，附带语音完整性检测和聊天倾向判断 |

---

## POST /asr

**描述**: 非流式语音识别接口。接收 base64 编码的音频数据，调用 ASR 引擎进行识别，返回识别出的文本。

**请求**:
- 方法: `POST`
- Content-Type: `application/json`

**请求体** (`asr_data` 模型):

| 字段 | 类型 | 必填 | 描述 |
|---|---|---|---|
| `audio` | string | 是 | base64 编码的音频数据 |

`audio` 字段支持两种格式：
- 纯 base64 字符串：`"UklGRiQA..."`
- 含 data URI 前缀的格式：`"data:audio/wav;base64,UklGRiQA..."`

服务端会自动检测并剥离 data URI 前缀（以 `,` 分割后取第二部分）。

**响应**:
- Content-Type: `application/json`
- 状态码: `200 OK`

**成功响应**（识别到文本）：

```json
{
  "text": "你好，今天天气怎么样？"
}
```

**识别为空时的响应**：

```json
{
  "text": null
}
```

| 字段 | 类型 | 描述 |
|---|---|---|
| `text` | string \| null | 识别出的文本内容，识别为空时返回 `null` |

**示例**:

```bash
# 纯 base64 格式
curl -X POST "http://localhost:8001/asr" \
  -H "Content-Type: application/json" \
  -d '{"audio": "UklGRiQAAABXQVZFZm10IBAAAAABAAEA..."}'
```

```bash
# 含 data URI 前缀格式
curl -X POST "http://localhost:8001/asr" \
  -H "Content-Type: application/json" \
  -d '{"audio": "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEA..."}'
```

**错误处理**:

| 状态码 | 场景 | 说明 |
|---|---|---|
| 422 | 请求体缺失或 `audio` 字段缺失 | 返回验证错误 |
| 500 | ASR 引擎处理异常 | 返回 `{"text": null}` |

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
      "loc": ["body", "audio"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

500 错误响应示例：

```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/json
```

```json
{
  "text": null
}
```

---

## WebSocket /asr_ws

**描述**: 实时流式语音识别接口。客户端通过 WebSocket 持续发送音频数据，服务端使用 Silero VAD 进行语音段落检测，在检测到完整语音段落后进行识别并返回纯文本结果。

**连接**:

```
ws://localhost:8001/asr_ws
```

### 客户端 → 服务端

客户端发送 JSON 格式的文本消息：

```json
{
  "type": "asr",
  "data": "<base64编码的音频数据>"
}
```

| 字段 | 类型 | 必填 | 描述 |
|---|---|---|---|
| `type` | string | 是 | 消息类型，固定为 `"asr"` |
| `data` | string | 是 | base64 编码的音频数据（int16 PCM 格式） |

**音频格式要求**:
- 编码格式: int16 PCM（16 位有符号整数）
- 采样率: 16000Hz
- base64 编码方式: 标准 base64（`base64.b64decode`）

### 服务端 → 客户端

服务端在检测到完整语音段落并识别成功后，发送纯文本消息：

```
你好，今天天气怎么样？
```

如果语音段落识别结果为空，服务端不会发送消息。

### 处理流程

1. 客户端持续发送音频数据帧
2. 服务端使用 Silero VAD（`speech_pad_ms=120`）检测语音活动
3. 当 VAD 检测到语音段落开始时，开始缓存音频数据
4. 当 VAD 检测到语音段落结束时，将缓存的音频合并为 WAV 格式
5. 调用 ASR 引擎识别，将结果以纯文本形式发送给客户端

**示例**:

```javascript
const ws = new WebSocket("ws://localhost:8001/asr_ws");

ws.onopen = () => {
  // 持续发送音频数据
  const audioChunk = getInt16PCMAudioChunk(); // int16 PCM 音频数据
  const base64Audio = btoa(String.fromCharCode(...new Uint8Array(audioChunk.buffer)));
  ws.send(JSON.stringify({
    type: "asr",
    data: base64Audio
  }));
};

ws.onmessage = (event) => {
  // 接收纯文本识别结果
  console.log("识别结果:", event.data);
};
```

### 错误处理

| 场景 | 服务端行为 |
|---|---|
| 客户端发送非 JSON 数据 | 记录警告日志，关闭连接 |
| `type` 字段不为 `"asr"` | 关闭连接 |
| 音频数据 base64 解码失败 | 记录警告日志，关闭连接 |
| 客户端异常断开 | 捕获异常，记录日志，清理 VAD 状态和音频缓冲区 |

---

## WebSocket /asr_ws_plus

**描述**: 增强版实时流式语音识别接口。在 `/asr_ws` 的基础上增加了两项功能：
- **语音完整性检测**（`isSpeakFinish`）：判断用户是否已经说完一句完整的话
- **聊天倾向判断**（`SpeakWithAssistant`）：判断用户的语音内容是否是在与 AI 助手对话

服务端会将多个语音段落的识别结果拼接，直到检测到语音完整后，再进行聊天倾向判断并返回结果。

**连接**:

```
ws://localhost:8001/asr_ws_plus
```

### 客户端 → 服务端

客户端发送的消息格式与 `/asr_ws` 完全相同：

```json
{
  "type": "asr",
  "data": "<base64编码的音频数据>"
}
```

| 字段 | 类型 | 必填 | 描述 |
|---|---|---|---|
| `type` | string | 是 | 消息类型，固定为 `"asr"` |
| `data` | string | 是 | base64 编码的音频数据（int16 PCM 格式） |

**音频格式要求**:
- 编码格式: int16 PCM（16 位有符号整数）
- 采样率: 16000Hz
- base64 编码方式: 标准 base64（`base64.b64decode`）

### 服务端 → 客户端

服务端在语音完整性检测通过且聊天倾向判断完成后，发送 JSON 格式的文本消息：

```json
{
  "type": "asr",
  "data": "你好，今天天气怎么样？",
  "withAssistant": true
}
```

| 字段 | 类型 | 描述 |
|---|---|---|
| `type` | string | 消息类型，固定为 `"asr"` |
| `data` | string | 完整的识别文本（可能由多个语音段落拼接而成） |
| `withAssistant` | boolean | 聊天倾向判断结果。`true` 表示用户在与 AI 助手对话（概率 ≥ 0.5），`false` 表示非对话内容 |

### 处理流程

1. 客户端持续发送音频数据帧
2. 服务端使用 Silero VAD（`speech_pad_ms=120`）检测语音活动
3. 当 VAD 检测到完整语音段落后，调用 ASR 引擎识别并缓存结果
4. 将所有已缓存的识别结果拼接，调用 `isSpeakFinish` 判断语音是否完整
5. 若语音不完整，继续等待下一个语音段落
6. 若语音完整，调用 `SpeakWithAssistant` 进行聊天倾向判断
7. 将拼接后的完整文本和聊天倾向结果以 JSON 格式发送给客户端
8. 清空识别结果缓存，开始下一轮检测

**示例**:

```javascript
const ws = new WebSocket("ws://localhost:8001/asr_ws_plus");

ws.onopen = () => {
  // 持续发送音频数据
  const audioChunk = getInt16PCMAudioChunk();
  const base64Audio = btoa(String.fromCharCode(...new Uint8Array(audioChunk.buffer)));
  ws.send(JSON.stringify({
    type: "asr",
    data: base64Audio
  }));
};

ws.onmessage = (event) => {
  const result = JSON.parse(event.data);
  console.log("识别文本:", result.data);
  console.log("是否与助手对话:", result.withAssistant);

  if (result.withAssistant) {
    // 用户在与 AI 助手对话，触发聊天流程
    startChat(result.data);
  }
};
```

### 错误处理

| 场景 | 服务端行为 |
|---|---|
| 客户端发送非 JSON 数据 | 记录警告日志，关闭连接 |
| `type` 字段不为 `"asr"` | 关闭连接 |
| 音频数据 base64 解码失败 | 记录警告日志，关闭连接 |
| 客户端异常断开 | 捕获异常，记录日志，清理 VAD 状态、音频缓冲区和识别结果缓存 |

---

## WebSocket 断连处理

两个 WebSocket 端点（`/asr_ws` 和 `/asr_ws_plus`）共享相同的断连处理机制：

1. **异常捕获**: 当客户端异常断开时（如网络中断、客户端崩溃），服务端通过 `try/except` 捕获 `receive_text()` 抛出的异常
2. **日志记录**: 记录客户端下线信息，包含异常详情（如 `"asr客户端下线：<异常信息>"`）
3. **资源清理**: 函数返回后，Python 垃圾回收机制自动清理 VAD 迭代器、音频缓冲区等局部资源

客户端应实现自动重连机制以应对网络不稳定的情况。
