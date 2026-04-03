# 配置接口文档

本文档描述 MoeChat 的配置管理 API 端点。该接口用于获取服务端当前的完整运行时配置信息。

---

## 端点概览

| 端点 | 方法 | 说明 |
|---|---|---|
| `/get_config` | POST | 获取当前完整运行时配置 |

---

## POST /get_config

**描述**: 获取服务端当前的完整运行时配置。返回 `config.yaml` 中加载的所有配置项，包括 LLM 端点、TTS 设置、SLM 配置等。该端点无需任何请求参数。

**请求**:
- 方法: `POST`
- Content-Type: `application/json`（请求体为空或可省略）

**请求参数**: 无

**响应**:
- Content-Type: `application/json`
- 状态码: `200 OK`

**响应体**: 返回完整的配置 JSON 对象，结构与 `config.yaml` 一致。

**响应示例**:

```json
{
  "LLM": {
    "base_url": "https://api.example.com/v1",
    "api_key": "sk-xxx",
    "model": "gpt-4o-mini"
  },
  "TTS": {
    "url": "http://localhost:9880",
    "ref_audio": "reference.wav"
  },
  "Agent": {
    "is_up": true,
    "name": "Chat酱"
  }
}
```

> **注意**: 以上响应示例仅展示部分配置字段，实际返回的配置对象包含所有运行时配置项，具体字段取决于 `config.yaml` 的内容。

**示例**:

```bash
curl -X POST "http://localhost:8001/get_config"
```

**错误处理**:

| 状态码 | 场景 | 说明 |
|---|---|---|
| 422 | 请求体格式不是有效的 JSON（如发送了非法内容） | 返回验证错误 |

> 由于该端点不接受任何请求参数，正常使用下不太可能触发 422 错误。仅在客户端发送了格式异常的请求体时才可能出现。

422 错误响应示例：

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
