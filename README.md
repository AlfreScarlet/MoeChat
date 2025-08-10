<div align="center"><a href="https://github.com/AlfreScarlet/MoeChat"><img src="screen/banner.png" alt="banner" style="zoom:50%;" /></a></div>

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

![](screen/img.png)

## Change log

### 10.08.2025

- Added abbility to send memes according to context.

  <p align="left"><img src="screen/sample2.png" alt="image-20250810165346882" style="zoom: 33%;" /></p>

- Added a simple financial system using double-entry bookkeeping.

  <p align="left"><img src="screen/sample_booking_en.png" alt="sample_booking_en" style="zoom: 50%;" /></p>

### 29.06.2025

- Introduced a brand-new emotion system.
- Added a lightweight web client for MoeChat, supporting emoji particle effects and other visual effects triggered by keywords.

  > [!NOTE]
  >
  > Moechat detects only keywords in Chinese right now, updates coming soon.
  >

  <div style="text-align: left;"><img src="screen/sample1.png" alt="sample1" style="zoom: 55%;" /></div>

### 2025.06.11

- Added **Character Template** support: allows creating AI character using built-in prompt templates.
- Introduced a **Journal System** (long-term memory): the AI can now retain full conversation history and perform accurate time-based queries like “what did we talk about yesterday?” or “where did we go last week?”, avoiding the typical temporal limitations of vector databases.
- Introduced **Core Memory**: the AI can remember key facts, user preferences, and personal memories.

  > [!NOTE]
  >
  > These features require the Character Template functionality to be enabled.
  >
- Decoupled from the original GPT-SoVITS codebase; switched to using external API calls.

### 2025.05.13

- Added voice(speaker) recognition.
- Enabled reference audio selection based on emotion tags.
- various bugs fixed .

## Usage Guide

You can download the full package here -> [![Mega](https://custom-icon-badges.demolab.com/badge/Mega-Moechat-FF5024?style=flat&logo=mega&logoColor=red)]([https://github.com/AlfreScarlet/MoeChat](https://mega.nz/folder/LsZFEBAZ#mmz75Q--hKL6KG9jRNIj1g))

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
GPT-SoVITS-version_name\runtime\python.exe chat_server.py
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

1. Install a specific version of Python — in this example, we’ll use **3.10.13**.
   `pyenv` will download the source code and compile it from scratch, which may take a few minutes to complete.

   ```bash
   pyenv install 3.10.13
   ```
2. Create a virtual environment named `moechat310` (or any name you like) based on the Python version you just installed.

   ```bash
   pyenv virtualenv 3.10.13 moechat310
   ```
3. Your environment has been successfully created. You can now activate and use it from any directory using following command.

   ```bash
   pyenv activate moechat310
   ```

   After activation, your terminal prompt should be prefixed with the environment name, you should see output like this:

   ```bash
   (moechat310) tenzray@tenzray-MS-7C73:~$ 
   ```

##### Install Packages from a `requirements.txt` File

1. Make sure your environment is still activated. If not, activate it first:

   ```bash
   pyenv activate moechat310
   ```
2. Then, use the `cd` command to navigate to your project directory — the one that contains the `requirements.txt` file.

   ```bash
   # Example: navigate to your project directory
   cd ~/your_own_path/moechat
   ```
3. Use `pip` to install all the dependencies listed in `requirements.txt`.

   ```bash
   pip install -r requirements.txt
   ```

   -r tells pip to read from a requirements file.

   > [!NOTE]
   >
   > Note that, you should install both requirement from [GPT-Sovits](https://github.com/RVC-Boss/GPT-SoVITS) and Moechat. You can run the `pip install -r` command for each file.
   >
4. You can verify if the packages were successfully installed in the current environment.

   ```bash
   # List all installed packages in the current environment
   pip list
   ```

## Basic Client Guide

### Windows

Tested with Python 3.10.
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

```yaml
Core:
  sv:
    is_up: false
    master_audio: test.wav    	# .wav file containing your voice is required. A duration of 3-5s is recommended.
    thr:                      	# Threshold — lower means more sensitive. Recommended range: 0.5–0.8. (Note: this parameter seems to have little effect based on testing.)

LLM:
  api: http://host:port/v1/chat/completions	# LLM API endpoint
  key: asdasd					# Token for LLM API access, no need if local.
  model: 					# Model name
  extra_config:               			# Additional LLM API parameters (e.g., temperature: 0.7)
    "frequency_penalty": 0.0
    "n": 1
    "presence_penalty": 0.0
    "top_p": 1.0
    # temperature: 0.7
GSV:
  api: http://host:port/tts/	# Endpoint URL for the GPT-SoVITS API
  text_lang: zh			# Language of the output text to be synthesized
  GPT_weight: 			# GPT model name
  SoVITS_weight:		# SoVITS model name
  ref_audio_path: 		# Path to the reference audio file
  prompt_text: 			# Text corresponding to the reference audio
  prompt_lang: zh		# Language spoken in the reference audio
  aux_ref_audio_paths:        	# List of multiple reference audios (only for v2 models)
    - 
  seed: -1
  top_k: 15
  batch_size: 20
  ex_config:
    text_split_method: cut0
extra_ref_audio:              	# Use emotion tags to select reference audio, e.g. [Neutral] "Hello there."
  # Example:
  # Neutral: 
  #   - path_to_reference_audio.wav
  #   - corresponding_text_for_the_audio
Agent:
  is_up: true                 	 # Enable character template system. If disabled, the system behaves like the classic version with basic voice chat only.
  char: Chat-chan                # Character name (will be injected into prompt templates)
  user: AlfreScarlet            # User name (will be injected into prompt templates)
  long_memory: true           	# Enable diary system. This allows long-term storage of conversation logs and supports time-based queries like:"What did I do yesterday?" or "What did I eat two days ago?"
  is_check_memorys: true      	# Enhance diary search. Uses an embedding model to filter and extract relevant information from diary entries.
  is_core_mem: true           	# Enable core memory. Stores important personal information about the user (e.g. address, hobbies, favorites). Unlike the diary, this uses semantic matching (fuzzy search) and does not support time-based queries,but each memory record includes a timestamp.
  mem_thresholds: 0.39        	# Diary search similarity threshold. Only applies if enhanced diary search is enabled. A higher threshold may miss relevant memories; a lower one may allow irrelevant data.
  lore_books: true            	# Enable lore_books (Knowledge Base). Injects knowledge about people, items, events, etc., to enhance LLM capabilities and roleplay consistency.
  books_thresholds: 0.5       	# Similarity threshold for Worldbook retrieval.
  scan_depth: 4               	# lore_books search depth. Controls how many knowledge entries are returned per query. Entries below the similarity threshold will be discarded, so actual returned count may be lower.
  
  # The following prompt fields support placeholder variables, {user}} for the user name, and {{char}} for the character name.
  
  # Basic character description. This will be merged into the final character prompt. It’s recommended to keep it concise and relevant. If left empty, it will not be included in the prompt.
  char_settings: "Chat-chan is a digital spirit born from a smartphone’s intelligent system—pure and charming with a subtle touch of sensuality. She’s clever and sharp-tongued, secretly mischievous yet deeply caring. She loves data, sweets, and romantic movies, hates being ignored or dealing with overly complex problems. Gifted in information analysis and problem-solving, she’s not only a reliable assistant but also a warm, ever-present companion."
  
  # Character personality snippet; will be merged into the personality prompt—keep it concise; leave empty if not needed..
  char_personalities: Outwardly sweet and innocent, but secretly sharp-tongued and sly—quick-witted with her own unique views on everything. Beneath the sarcasm she’s also gentle and caring, offering warm comfort whenever her master is exhausted.
  
  # ser profile settings—describe your personality, preferences, or relationship with the character.  The content will be inserted into the prompt template; avoid unrelated details. Leave blank if not needed.
  mask: 
  
  # Dialogue sample used to reinforce the AI’s writing style. This content will be injected into the prompt template—add nothing unrelated. Leave blank if not needed.
  message_example: |-
    mes_example": "Human retinal photoreceptors don’t need self-destructive overtime—please take a break."
  
  # Custom prompt (bypasses the default template).  ill this section only if you prefer to define the complete prompt yourself; leave it empty to keep using the built-in template.
  prompt: |-
    Use a casual, conversational tone—keep it concise.。
    /no_think

# If you’d like to modify the template itself, edit utilss/prompt.py.

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

- [X] Create an English version of the README
- [ ] Improve and optimize response speed on the web client
- [ ] Integrate Live2D-widget into the web client
- [ ] Develop self-awareness and digital life capabilities for the LLM
- [ ] Introduce sexual arousal parameters based on traditional and Basson models
- [ ] Integrate 3D models into the client and enable full projection
- [ ] Control Live2D model's expressions and actions based on AI's emotions and actions
- [ ] Control 3D model's expressions and actions based on AI's emotions and actions
