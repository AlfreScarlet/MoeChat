# 语音活动检测（VAD）接口文档

本文档描述 MoeChat 的语音活动检测（Voice Activity Detection）API 端点。该接口通过 WebSocket 接收客户端发送的音频数据，使用 Silero VAD 模型实时检测语音活动的起止，并以纯文本消息通知客户端。

---

## 端点概览

| 端点 | 方法 | 说明 |
|---|---|---|
| `/api/ws` | WebSocket | 实时语音活动检测，检测语音段落的开始和结束 |

---

## WebSocket /api/ws

**描述**: 实时语音活动检测接口。客户端通过 WebSocket 持续发送音频数据，服务端使用 Silero VAD（`speech_pad_ms=90`）对音频进行语音活动检测，当检测到语音段落的开始或结束时，向客户端发送纯文本通知消息。

**连接**:

```
ws://localhost:8001/api/ws
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
| `data` | string | 是 | base64 编码的音频数据（float32 采样） |

**音频格式要求**:
- 编码格式: float32（32 位浮点数）
- 采样率: 16000Hz
- base64 编码方式: URL 安全 base64（`base64.urlsafe_b64decode`）

> **注意**: 与 ASR 接口（`/asr_ws`、`/asr_ws_plus`）不同，VAD 接口使用 `urlsafe_b64decode` 进行 base64 解码，而非标准的 `b64decode`。URL 安全 base64 使用 `-` 和 `_` 替代标准 base64 中的 `+` 和 `/`。客户端在编码音频数据时需使用对应的 URL 安全 base64 编码方式。

### 服务端 → 客户端

服务端在检测到语音活动状态变化时，发送纯文本消息：

**检测到语音开始**:

```
开始说话...
```

**检测到语音结束**:

```
结束说话
```

| 消息 | 含义 |
|---|---|
| `开始说话...` | VAD 检测到语音段落开始，用户正在说话 |
| `结束说话` | VAD 检测到语音段落结束，用户停止说话 |

### 处理流程

1. 客户端建立 WebSocket 连接，服务端初始化 Silero VAD 迭代器（`speech_pad_ms=90`）
2. 客户端持续发送包含音频数据的 JSON 消息
3. 服务端对每帧音频数据使用 URL 安全 base64 解码，转换为 float32 numpy 数组
4. 将音频数据传入 VAD 迭代器进行语音活动检测
5. 当 VAD 检测到语音段落开始（`"start"` 事件）时，发送 `"开始说话..."`
6. 当 VAD 检测到语音段落结束（`"end"` 事件）时，发送 `"结束说话"`
7. 循环处理，直到连接关闭

**示例**:

```javascript
const ws = new WebSocket("ws://localhost:8001/api/ws");

ws.onopen = () => {
  // 持续发送音频数据
  const audioChunk = getFloat32AudioChunk(); // float32 音频数据，采样率 16000Hz
  // 使用 URL 安全 base64 编码
  const base64Audio = base64UrlEncode(new Uint8Array(audioChunk.buffer));
  ws.send(JSON.stringify({
    type: "asr",
    data: base64Audio
  }));
};

ws.onmessage = (event) => {
  if (event.data === "开始说话...") {
    console.log("用户开始说话");
    // 可在此处开始录音或触发 UI 反馈
  } else if (event.data === "结束说话") {
    console.log("用户停止说话");
    // 可在此处停止录音或触发后续处理
  }
};

// URL 安全 base64 编码辅助函数
function base64UrlEncode(uint8Array) {
  const base64 = btoa(String.fromCharCode(...uint8Array));
  return base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
```

### 错误处理

| 场景 | 服务端行为 |
|---|---|
| 客户端发送非 JSON 数据 | 捕获异常，断开连接 |
| 音频数据 base64 解码失败 | 捕获异常，断开连接 |
| 客户端异常断开 | 捕获异常，退出处理循环，清理 VAD 迭代器等资源 |

---

## WebSocket 断连处理

当客户端异常断开时（如网络中断、客户端崩溃），服务端的处理行为如下：

1. **异常捕获**: 服务端通过 `try/except` 捕获 `receive_text()` 或数据处理过程中抛出的异常
2. **退出循环**: 捕获到异常后，服务端跳出消息处理循环（`break`）
3. **资源清理**: 函数返回后，Python 垃圾回收机制自动清理 VAD 迭代器（`VADIterator`）等局部资源

客户端应实现自动重连机制以应对网络不稳定的情况。
