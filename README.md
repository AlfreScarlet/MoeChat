<div align="center"><a href="https://github.com/AlfreScarlet/MoeChat"><img src="/doc/screen/banner.png" alt="banner" style="zoom:50%;" /></a></div>

<div align="center">

[![百度云](https://custom-icon-badges.demolab.com/badge/百度云-Link-4169E1?style=flat&logo=baidunetdisk)](https://pan.baidu.com/share/init?surl=mf6hHJt8hVW3G2Yp2gC3Sw&pwd=2333)
[![QQ群](https://custom-icon-badges.demolab.com/badge/QQ群-967981851-00BFFF?style=flat&logo=tencent-qq)](https://qm.qq.com/q/6pfdCFxJcc)
[![BiliBili](https://custom-icon-badges.demolab.com/badge/BiliBili-芙兰蠢兔-FF69B4?style=flat&logo=bilibili)](https://space.bilibili.com/3156308)
[![Mega](https://custom-icon-badges.demolab.com/badge/Mega-Moechat-FF5024?style=flat&logo=mega&logoColor=red)](https://mega.nz/folder/LsZFEBAZ#mmz75Q--hKL6KG9jRNIj1g)

<!--[![Discord](https://custom-icon-badges.demolab.com/badge/Discord-Moechat-FF5024?style=flat&logo=Discord)](https://discord.gg/2JJ6J2T9P7) -->

<a href="/README.md">English</a> |
<a href="doc/README_zh.md">Chinese</a>

</div>

# Voice Interaction System Powered by GPT-SoVITS

## Overview

A powerful voice interaction system designed for natural conversations and immersive roleplay with AI characters.

## Features

- Using GPT-SoVITS as the TTS (Text-to-Speech) module.
- Integrates an ASR interface, with FunASR as the underlying speech recognition engine.
- MoeChat supports any LLM API that follows the **OpenAI specification**.
- On Linux, first-token latency is usually under 1.5 seconds; on Windows, around 2.1 seconds.
- MoeChat delivers the **fastest** and **most precise** long-term memory retrieval across platforms. It supports precise memory queries based on fuzzy time expressions such as "yesterday" or "last week." On a laptop with an Intel 11800H CPU, the total query time averages around 80ms.
- Moe chat has the ability to selects reference audio dynamically based on emotional context.

## Testing Platform

#### Server site

- OS: Manjaro Linux
- CPU: AMD Ryzen 9 5950X
- GPU: NVIDIA RTX 3080 Ti

#### Client site

- Raspberry Pi 5

### Test Results

![](/doc/screen/img.png)

## Change log

### 10.08.2025

- Added abbility to send memes according to context.

  <p align="left"><img src="/doc/screen/sample2.png" alt="image-20250810165346882" style="zoom: 33%;" /></p>

- Added a simple financial system using double-entry bookkeeping.

  <p align="left"><img src="/doc/screen/sample_booking_en.png" alt="sample_booking_en" style="zoom: 50%;" /></p>

### 29.06.2025

- Introduced a brand-new emotion system.
- Added a lightweight web client for MoeChat, supporting emoji particle effects and other visual effects triggered by keywords.

  > [!NOTE]
  >
  > Moechat detects only keywords in Chinese right now, updates coming soon.

  <div style="text-align: left;"><img src="/doc/screen/sample1.png" alt="sample1" style="zoom: 55%;" /></div>

### 2025.06.11

- Added **Character Template** support: allows creating AI character using built-in prompt templates.
- Introduced a **Journal System** (long-term memory): the AI can now retain full conversation history and perform accurate time-based queries like “what did we talk about yesterday?” or “where did we go last week?”, avoiding the typical temporal limitations of vector databases.
- Introduced **Core Memory**: the AI can remember key facts, user preferences, and personal memories.

  > [!NOTE]
  >
  > These features require the Character Template functionality to be enabled.

- Decoupled from the original GPT-SoVITS codebase; switched to using external API calls.

### 2025.05.13

- Added voice(speaker) recognition.
- Enabled reference audio selection based on emotion tags.
- various bugs fixed .

## Usage Guide

You can download the full package here -> [![Mega](https://custom-icon-badges.demolab.com/badge/Mega-Moechat-FF5024?style=flat&logo=mega&logoColor=red)](<[https://github.com/AlfreScarlet/MoeChat](https://mega.nz/folder/LsZFEBAZ#mmz75Q--hKL6KG9jRNIj1g)>)

<!--Join our Discord server to discuss：[![Discord](https://custom-icon-badges.demolab.com/badge/Discord-Moechat-FF5024?style=flat&logo=Discord)](https://discord.gg/2JJ6J2T9P7)-->

However, You are encourage to fork your own copy from [GPT-Sovits](https://github.com/RVC-Boss/GPT-SoVITS) or download a release from there..

### Windows

##### Launching the GPT-SoVITS server

1. Place your `GPT-SoVITS` folder alongside your MoeChat directory for convenience.
2. Open a terminal in the `GPT-SoVITS-version_name` folder.
3. Ensure that `api_v2.py` exists in the root of that directory.
4. Run the following command to launch the API server of [GPT-Sovits](https://github.com/RVC-Boss/GPT-SoVITS)

```bash
runtime\python.exe api_v2.py
```

##### launch MoeChat server

1. lauch Moechat server at root directory of Moechat.
2. Run the following command.

```bash
uv sync
uv run main_web.py
```

### Linux (Ubuntu / Debian / Linux Mint)

##### Foreword

> [!IMPORTANT]
>
> It is recommanded to set up a powerful, isolated, and flexible Python development environment that you can access from **any directory**.
> We will be using **`pyenv`**to manage multiple Python versions, along with its **`pyenv-virtualenv`** plug-in to create dedicated virtual environments for different project.

> [!WARNING]
>
> Heads up: The commands below modify your environment and system configuration. Know what you’re doing before you run anything. If you blindly copy-paste stuff and break your system — that’s on you, not me 😎.

##### Install Build Dependencies

`pyenv` installs Python from source, so system-level compilers and development headers must be installed first.

```bash
sudo apt install -y make build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev curl \
llvm libncursesw5-dev xz-utils tk-dev \
libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev git
```

##### Install Pyenv & Essential Plugins

We recommend using the official installer script to install `pyenv` and its commonly used plugins (such as `pyenv-virtualenv`).
This script installs all components into the `~/.pyenv` directory by default.

```bash
curl https://pyenv.run | bash
```

##### Configure Your Shell Environment

In order for your terminal to recognize the `pyenv` command, you must add its initialization code to your shell startup file (typically `~/.bashrc` or `~/.zshrc`).

```bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
```

To apply the changes, either close and reopen your terminal, or run the following command:

```bash
source ~/.bashrc
```

##### Create Your Python Environment

Now it's time to create your environment.

1. Install a specific version of Python — MoeChat requires **Python 3.11+**.
   `pyenv` will download the source code and compile it from scratch, which may take a few minutes to complete.

   ```bash
   pyenv install 3.11
   ```

2. Create a virtual environment named `moechat311` (or any name you like) based on the Python version you just installed.

   ```bash
   pyenv virtualenv 3.11 moechat311
   ```

3. Your environment has been successfully created. You can now activate and use it from any directory using following command.

   ```bash
   pyenv activate moechat311
   ```

   After activation, your terminal prompt should be prefixed with the environment name, you should see output like this:

   ```bash
   (moechat311) tenzray@tenzray-MS-7C73:~$
   ```

##### Install Packages with `uv`

1. Make sure your environment is still activated. If not, activate it first:

   ```bash
   pyenv activate moechat311
   ```

2. Then, use the `cd` command to navigate to your project directory — the one that contains `pyproject.toml`.

   ```bash
   # Example: navigate to your project directory
   cd ~/your_own_path/moechat
   ```

3. Use `uv` to install the project dependencies from `pyproject.toml`.

   ```bash
   uv sync
   ```

   > [!NOTE]
   >
   > GPT-SoVITS is still a separate service. Install and start its own dependencies from the GPT-SoVITS project before starting MoeChat.

4. You can verify if the packages were successfully installed in the current environment.

   ```bash
   uv run python -c "import sys; print(sys.version)"
   ```

## Basic Client Guide

### Windows

Tested with Python 3.11.
If you want to run the server and client separately (e.g. access the server remotely),
you can modify the IP address in lines 17 and 18 of the `client-gui/src/client_utils.py` file.

##### Simple GUI Client

- run following command:

```bash
GPT-SoVITS-version_name\runtime\python.exe client-gui\src\client_gui.py
```

### Linux

- You should have all environment satisfied and activated by now
  run following command:

```bash
python client-gui\src\client_gui.py
```

## Configuration

The package uses `config.yaml` as its default configuration file.
`config.example.yaml` contains a sanitized template. Do not commit real API keys; set your own local keys in `config.yaml`.

```yaml
Core:
  tt: false
  sv:
    is_up: false
    master_audio: test.wav
    thr: 0.5
  min_text_len: 10
  max_text_len: 40
LLM:
  api: https://api.siliconflow.cn/v1/chat/completions
  key: "" # Set your own OpenAI-compatible API key locally.
  model: Qwen/Qwen3-8B
  extra_config:
LLM2:
  api: https://api.siliconflow.cn/v1/chat/completions
  key: "" # Set your own OpenAI-compatible API key locally.
  model: Qwen/Qwen3-8B
  extra_config:
SLM:
  api: http://localhost:11434/v1/chat/completions
  key:
  model: qwen3:0.6b
  extra_config:
    temperature: 0.6
    stream: false
GSV:
  api: http://127.0.0.1:9880/tts
ASR:
  type: local
  api:
    url: http://localhost:11434/v1/chat/completions
    key:
    model: Qwen3-ASR-0.6B
```

## API Description

All endpoints use POST requests.

### ASR Speech Recognition API

```python
# URL: /api/asr
# Request Format: application/json
# Audio format is WAV with a sample rate of 16000, 16-bit depth, mono channel, and a frame length of 20ms.
# Encode the audio data as a URL-safe Base64 string and place it in the data field of the JSON body.
{
  "data": str # base64-encoded audio data
}
# Response: The server returns the recognized text directly.
```

### Chat Interface

```python
# The chat interface uses SSE streaming. The server slices the LLM response and generates corresponding audio data, returning them to the client in segments.
# Request format: JSON
# Place the LLM context data into the `msg` field as a list of strings.
# Request example:
{
  "msg": [
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hello, how can I help you?"},
    {"role": "user", "content": "How much is 1 + 1?"},
  ]
}

# Server response example:
{
  "file": str     # urlsafe base64-encoded audio file
  "message": str  # text corresponding to the audio data
  "done": False   # boolean indicating whether this is the last data packet
}
# The final data packet will include the full LLM response in the `message` field for context concatenation:
{
  "file": str
  "message": str  # full LLM response text for context
  "done": True    # boolean indicating this is the last data packet
}
```

### Chat Interface V2

```python
# The chat interface uses SSE streaming. The server slices the LLM response and generates corresponding audio data, returning them to the client in segments.
# Request format: JSON
# Place the LLM context data into the `msg` field as a list of strings.
# Request example:
{
  "msg": [
    {"role": "user", "content": "Hello!"},
  ]
}

# Server response example:
{
  "type": str     # type of response, text or audio.
  "data": str     # text or urlsafe base64-encoded audio file
  "done": False   # boolean indicating whether this is the last data packet
}
# The final data packet will include the full LLM response in the `message` field for context concatenation:
{
  "type": "text"
  "data": str     # full LLM response text for context
  "done": True    # boolean indicating this is the last data packet
}
```

## Goals

- [x] Create an English version of the README
- [ ] Improve and optimize response speed on the web client
- [ ] Integrate Live2D-widget into the web client
- [ ] Develop self-awareness and digital life capabilities for the LLM
- [ ] Introduce sexual arousal parameters based on traditional and Basson models
- [ ] Integrate 3D models into the client and enable full projection
- [ ] Control Live2D model's expressions and actions based on AI's emotions and actions
- [ ] Control 3D model's expressions and actions based on AI's emotions and actions

## License

Program Name: MoeChat
Copyright (C) 2025 芙兰蠢兔、Tenzray

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
