# 文本转语音（TTS）接口文档

本文档描述 MoeChat 的文本转语音（Text-to-Speech）API 端点。该接口接收文本输入，自动进行分句处理后逐句合成语音，以 SSE（Server-Sent Events）流式返回文本片段和对应的 base64 编码音频数据。

---

## 端点概览

| 端点 | 方法 | 说明 |
|---|---|---|
| `/gptsovits` | POST | 文本转语音接口，将文本分句后逐句合成并以 SSE 流式返回 |

---

## POST /gptsovits

**描述**: 文本转语音接口。接收待合成的文本字符串，内部通过 `remove_parentheses_content_and_split` 对文本进行预处理（去除括号内容并按标点符号分句），然后逐句调用 GPT-SoVITS 引擎合成语音，以 SSE 流式返回每句的文本和音频数据。

**请求**:
- 方法: `POST`
- Content-Type: `application/json`

**请求体** (`msg_data` 模型):

| 字段 | 类型 | 必填 | 描述 |
|---|---|---|---|
| `msg` | string | 是 | 待合成的文本字符串 |

**请求体示例**:

```json
{
  "msg": "你好！今天天气真不错，我们出去走走吧。"
}
```

**响应**:
- Content-Type: `text/event-stream`
- 状态码: `200 OK`

**SSE 数据帧格式**:

```
data: {"text": "你好！", "audio": "base64..."}\n\n
data: {"text": "今天天气真不错，", "audio": "base64..."}\n\n
data: {"text": "我们出去走走吧。", "audio": "base64..."}\n\n
```

每个 SSE 帧包含一个 JSON 对象：

| 字段 | 类型 | 描述 |
|---|---|---|
| `text` | string | 分句后的文本片段 |
| `audio` | string | 该文本片段对应的 TTS 合成音频数据（base64 编码） |

### 文本分句处理

输入文本在合成前会经过以下预处理：

1. **括号内容移除**: 去除文本中括号（包括中英文括号）及其内部的内容
2. **标点分句**: 按中英文标点符号（句号、问号、感叹号、省略号等）将文本切分为多个句子
3. **逐句合成**: 每个句子独立调用 TTS 引擎合成语音，合成完成后立即以 SSE 帧推送给客户端

如果某个句子的 TTS 合成结果为空（合成失败），该句子会被跳过，不会产生对应的 SSE 帧。

**示例**:

```bash
curl -N -X POST "http://localhost:8001/gptsovits" \
  -H "Content-Type: application/json" \
  -d '{"msg": "你好！今天天气真不错，我们出去走走吧。"}'
```

响应（SSE 流）：

```
data: {"text": "你好！", "audio": "UklGRiQA..."}\n\n
data: {"text": "今天天气真不错，", "audio": "UklGRkBA..."}\n\n
data: {"text": "我们出去走走吧。", "audio": "UklGRlgA..."}\n\n
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
