# MoeChat API 接口文档

## 概述

MoeChat 是一个开源的语音交互系统，支持与 AI 角色进行自然对话和沉浸式角色扮演。本文档提供 MoeChat 所有 API 接口的完整参考，涵盖 HTTP REST、WebSocket 和原生 TCP Socket 三种协议类型。

默认服务端口：
- HTTP API 服务：`8001`
- TCP Socket 服务：`8002`

---

## API 模块索引

| 模块 | 文档 | 协议类型 | 说明 |
|---|---|---|---|
| 聊天 | [chat.md](chat.md) | HTTP (SSE) | 流式聊天接口，支持 SSE 实时推送 |
| 语音识别 (ASR) | [asr.md](asr.md) | HTTP + WebSocket | 语音转文本，支持 HTTP 单次识别和 WebSocket 实时流式识别 |
| 文本转语音 (TTS) | [tts.md](tts.md) | HTTP (SSE) | 文本合成语音，SSE 流式返回音频片段 |
| 语音活动检测 (VAD) | [vad.md](vad.md) | WebSocket | 实时语音端点检测 |
| 助手管理 | [assistant.md](assistant.md) | HTTP | AI 角色的增删改查和资源管理 |
| 配置 | [config.md](config.md) | HTTP | 运行时配置读取 |
| 核心 | [core.md](core.md) | HTTP | 健康检查和版本信息 |
| Socket | [socket.md](socket.md) | 原生 TCP Socket | 基于自定义协议的实时语音交互 |

---

## 通用错误响应格式

所有 HTTP 端点共享以下错误响应格式。

### 422 验证错误

当请求参数缺失、类型错误或不满足约束条件时，FastAPI 返回标准的 `ValidationError` 响应：

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

`detail` 数组中每个元素包含：

| 字段 | 类型 | 说明 |
|---|---|---|
| `type` | string | 错误类型（如 `missing`、`string_type`、`value_error`） |
| `loc` | array | 错误位置路径（如 `["body", "field_name"]` 或 `["query", "param_name"]`） |
| `msg` | string | 人类可读的错误描述 |
| `input` | any | 客户端提供的原始输入值（缺失时为 `null`） |

### 404 资源不存在

当请求的资源（如助手、文件目录）不存在时返回：

```http
HTTP/1.1 404 Not Found
Content-Type: application/json
```

```json
{
  "detail": "助手不存在: example_name"
}
```

### 400 请求错误

当请求参数合法但业务逻辑不允许时返回（如无效的助手名称、损坏的 zip 文件）：

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json
```

```json
{
  "detail": "无效的助手名称"
}
```

### 500 服务端内部错误

当服务端处理过程中发生未预期的异常时返回：

```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/json
```

```json
{
  "detail": "内部服务器错误描述"
}
```

部分端点（如 ASR）在异常时可能返回：

```json
{
  "text": null
}
```

---

## WebSocket 连接说明

WebSocket 端点（ASR、VAD）在连接异常断开时，服务端会：

1. 捕获 `WebSocketDisconnect` 或其他连接异常
2. 记录警告日志
3. 清理相关资源（如 VAD 状态、音频缓冲区）

客户端应实现重连机制以应对网络不稳定的情况。

---

## Socket 协议说明

原生 TCP Socket 接口使用自定义文本协议，详见 [socket.md](socket.md)。消息以 `<|end|>` 作为分隔符，支持文本和音频两种消息类型。
