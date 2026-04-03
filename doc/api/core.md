# 核心接口文档

本文档描述 MoeChat 的核心系统 API 端点。该接口用于健康检查和版本信息查询。

---

## 端点概览

| 端点 | 方法 | 说明 |
|---|---|---|
| `/health` | GET | 健康检查，返回服务状态和版本号 |

---

## GET /health

**描述**: 健康检查端点。用于确认服务是否正常运行，同时返回当前项目版本号（从 `pyproject.toml` 中读取）。

**请求**:
- 方法: `GET`
- Content-Type: 无（无请求参数）

**请求参数**: 无

**响应**:
- Content-Type: `application/json`
- 状态码: `200 OK`

**响应体**:

| 字段 | 类型 | 描述 |
|---|---|---|
| `status` | string | 服务状态，固定值 `"ok"` |
| `version` | string | 项目版本号，从 `pyproject.toml` 读取；读取失败时返回 `"unknown"` |

**响应示例**:

```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

**示例**:

```bash
curl "http://localhost:8001/health"
```

**错误处理**:

该端点不接受任何请求参数，正常情况下不会返回客户端错误。仅在服务端内部异常时可能返回 500 错误：

| 状态码 | 场景 | 说明 |
|---|---|---|
| 500 | 服务端内部错误（如版本信息读取异常） | 返回错误信息 |

500 错误响应示例：

```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/json
```

```json
{
  "detail": "Internal Server Error"
}
```
