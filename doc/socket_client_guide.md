# MoeChat Socket 客户端接入文档

## 连接信息

| 项目 | 值 |
|---|---|
| 协议 | TCP Socket |
| 默认地址 | `0.0.0.0:8002` |
| 超时 | 服务端对每个连接设置 5 秒 recv 超时 |

---

## 消息帧格式

所有消息（客户端→服务端、服务端→客户端）均使用统一的帧格式：

```
<|标签|>载荷<|end|>
```

- `<|标签|>` — 消息类型标识
- `载荷` — 文本（UTF-8）或二进制数据
- `<|end|>` — 帧结束分隔符

一次 TCP recv 可能包含多个帧或不完整帧，客户端必须自行缓冲并按 `<|end|>` 切分。

---

## 客户端 → 服务端

### 1. 发送音频流（语音输入）

用于实时语音识别场景。客户端持续发送麦克风采集的音频帧，服务端内部进行 VAD 检测和 ASR 识别。

```
<|audio|>{raw_pcm_bytes}<|end|>
```

音频格式要求：

| 参数 | 值 |
|---|---|
| 采样率 | 16000 Hz |
| 位深 | 16-bit (int16) |
| 声道 | 单声道 (mono) |
| 编码 | 原始 PCM (little-endian) |

建议每帧发送 20ms 的数据（即 640 字节 = 320 个 int16 采样点）。服务端内部会缓冲至 240 个采样点后送入 VAD。

### 2. 发送文本消息（直接对话）

跳过 ASR，直接将文本发送给 LLM 进行对话：

```
<|me|>{UTF-8文本}<|end|>
```

示例（Python bytes）：

```python
msg = "你好"
client_socket.sendall(f"<|me|>{msg}<|end|>".encode("utf-8"))
```

---

## 服务端 → 客户端

### 1. `<|start|>` — 语音活动开始（打断信号）

当 VAD 检测到用户开始说话时发送。客户端收到后应立即停止当前正在播放的音频，准备接收新的回复。

```
<|start|><|end|>
```

### 2. `<|me|>` — ASR 识别结果

VAD 检测到用户说完一句话后，服务端完成 ASR 识别并返回文本：

```
<|me|>{识别文本}<|end|>
```

客户端可将此文本显示为用户消息气泡。

### 3. `<|text|>` — LLM 流式文本

LLM 生成的文本片段，逐句/逐块推送。客户端可实时显示打字效果：

```
<|text|>{文本片段}<|end|>
```

注意：文本是分块到达的，不是一次性完整回复。

### 4. `<|audio|>` — TTS 音频数据

与文本对应的语音合成音频，为原始 PCM 字节流（由 GPT-SoVITS 生成的 raw 格式）。客户端应按顺序播放：

```
<|audio|>{raw_audio_bytes}<|end|>
```

### 5. `<|complete|>` — 回复结束

表示当前轮对话的 LLM + TTS 全部处理完毕：

```
<|complete|><|end|>
```

客户端收到后可恢复录音状态，等待用户下一次输入。

---

## 交互时序

### 语音对话流程

```
客户端                              服务端
  │                                   │
  │──<|audio|>{pcm}<|end|>──────────>│  (持续发送音频帧)
  │──<|audio|>{pcm}<|end|>──────────>│
  │  ...                              │
  │<──<|start|><|end|>───────────────│  (VAD检测到开始说话，打断信号)
  │──<|audio|>{pcm}<|end|>──────────>│  (继续发送)
  │  ...                              │
  │<──<|me|>你好<|end|>──────────────│  (VAD检测到说完，ASR结果)
  │                                   │
  │<──<|text|>你好呀<|end|>──────────│  (LLM流式文本)
  │<──<|text|>，今天...<|end|>───────│
  │<──<|audio|>{pcm}<|end|>──────────│  (TTS音频)
  │<──<|text|>怎么样？<|end|>────────│
  │<──<|audio|>{pcm}<|end|>──────────│
  │<──<|complete|><|end|>────────────│  (本轮结束)
  │                                   │
```

### 文本对话流程

```
客户端                              服务端
  │                                   │
  │──<|me|>你好<|end|>──────────────>│  (发送文本)
  │                                   │
  │<──<|text|>你好呀<|end|>──────────│  (LLM流式文本)
  │<──<|audio|>{pcm}<|end|>──────────│  (TTS音频)
  │<──<|complete|><|end|>────────────│  (本轮结束)
  │                                   │
```

---

## 客户端实现要点

### 帧解析器

TCP 是流式协议，必须实现缓冲区 + 分隔符切分：

```python
class FrameParser:
    DELIMITER = b"<|end|>"

    def __init__(self):
        self.buffer = b""

    def feed(self, data: bytes) -> list[bytes]:
        """喂入数据，返回完整帧列表"""
        self.buffer += data
        frames = []
        while True:
            idx = self.buffer.find(self.DELIMITER)
            if idx == -1:
                break
            frame = self.buffer[:idx]
            self.buffer = self.buffer[idx + len(self.DELIMITER):]
            if frame:
                frames.append(frame)
        return frames
```

### 帧分发

```python
def dispatch_frame(frame: bytes):
    if frame.startswith(b"<|start|>"):
        # 打断：停止当前音频播放
        stop_playback()

    elif frame.startswith(b"<|me|>"):
        text = frame[len(b"<|me|>"):].decode("utf-8")
        # 显示ASR识别结果
        show_user_message(text)

    elif frame.startswith(b"<|text|>"):
        text = frame[len(b"<|text|>"):].decode("utf-8")
        # 追加显示LLM文本
        append_assistant_text(text)

    elif frame.startswith(b"<|audio|>"):
        audio_data = frame[len(b"<|audio|>"):]
        # 将音频数据加入播放队列
        enqueue_audio(audio_data)

    elif frame.startswith(b"<|complete|>"):
        # 本轮对话结束
        on_turn_complete()
```

### 打断机制

收到 `<|start|>` 时，客户端应：
1. 立即停止正在播放的 TTS 音频
2. 清空音频播放队列
3. 清空未显示完的文本缓冲

服务端会自动取消上一轮的 LLM/TTS 任务。

### 音频采集建议

```python
import pyaudio

RATE = 16000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK = 320  # 20ms @ 16kHz

stream = audio.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, input=True, frames_per_buffer=CHUNK)

while recording:
    pcm_data = stream.read(CHUNK)
    client_socket.sendall(b"<|audio|>" + pcm_data + b"<|end|>")
```

---

## 注意事项

- 服务端 recv 超时为 5 秒。如果客户端长时间不发送数据，连接可能断开。语音模式下持续发送音频帧即可保活；纯文本模式下需要考虑心跳或在发送前重连。
- `<|text|>` 和 `<|audio|>` 是异步到达的，文本通常先于对应音频到达。客户端可以先显示文本，音频到达后再播放。
- 服务端同一时间只处理一个对话任务。发送新消息会自动取消上一轮未完成的任务。
- 音频帧不要求严格的 20ms 对齐，但每帧不应过大（建议不超过 1024 字节），否则可能影响 VAD 实时性。
