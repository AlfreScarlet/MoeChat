<p align="left"><img src="/screen/logo1.png" alt="logo1" style="zoom:20%;" /></p>

![banner](/screen/banner.png)



[![百度云](https://custom-icon-badges.demolab.com/badge/百度云-Link-4169E1?style=flat&logo=baidunetdisk)](https://pan.baidu.com/share/init?surl=mf6hHJt8hVW3G2Yp2gC3Sw&pwd=2333)
[![QQ群](https://custom-icon-badges.demolab.com/badge/QQ群-967981851-00BFFF?style=flat&logo=tencent-qq)](https://qm.qq.com/q/6pfdCFxJcc)
[![BiliBili](https://custom-icon-badges.demolab.com/badge/BiliBili-芙兰蠢兔-FF69B4?style=flat&logo=bilibili)](https://space.bilibili.com/3156308)
[![Discord](https://custom-icon-badges.demolab.com/badge/Discord-Moechat-FF5024?style=flat&logo=Discord)](https://discord.gg/2JJ6J2T9P7)

  <a href="/README.md">English</a> |
  <a href="doc/README_zh.md">Chinese</a>

</div>

# 基于GPT-SoVITS的语音交互系统

## 简介

一个强大的语音交互系统，用语音和AI角色自然对话、沉浸扮演。

## 特点

- 本项目使用GPT-SoVITS作为TTS模块。
- 集成ASR接口，使用funasr作为语音识别模块基础。
- Moechat支持所有openai规范的大语言模型接口。
- Linux环境下首Token延迟基本能做到1.5s以内。Windows环境下延迟在2.1s左右。
- Moechat项目拥有全站**最快**、**最精准**的长期记忆查询，可根据如“昨天”、“上周”这样的模糊的时间范围精确查询记忆，在11800h CPU的笔记本上测试，查询总耗时仅为80ms左右。
- 根据情绪选择对应的参考音频。

## 测试平台

#### 服务端

- OS：Manjaro
- CPU：R9 5950X
- GPU：RTX 3080ti

#### 客户端

- 树莓派5

### 测试结果

![](/screen/img.png)

## 更新日志

### 10.08.2025

- Moechat现在可以发送表情包了。

  <p align="left"><img src="/screen/sample2.png" alt="image-20250810165346882" style="zoom: 33%;" /></p>

- 添加了简单的财务系统，使用复式记账。

  <p align="left"><img src="/screen/sample_booking_zh.png" alt="sample_booking_zh" style="zoom: 50%;" /></p>

### 2025.06.29

- 设计了全新的情绪系统。
- 为Moechat添加了简易的web端，可以识别关键词进行表情飘屏，和其他例子特效。

  <div style="text-align: left;"><img src="/screen/sample1.png" alt="sample1" style="zoom: 55%;" /></div>

### 2025.06.11

- 增加角色模板功能：可以使用内置提示词模板创建角色。
- 增加日记系统（长期记忆：AI可以记住所有的聊天内容，并且可以使用像”昨天聊了什么“、”上周去了哪里“和”今天中午吃了什么“这样的语句进行基于时间范围的精确查询，不会像传统向量数据库那样因为时间维度而丢失记忆。
- 增加核心记忆功能：AI可以记住关于用户的重要回忆、信息和个人喜好。

  上述功均需要启用角色模板功能
- 脱离原有的GPT-SoVITS代码，改为API接口调用

### 2025.05.13

- 新增声纹识别
- 新增了根据情绪标签选择指定参考音频。
- 修复了一些bug。

## 整合包使用说明

网盘下载链接：[![BaiduPan](https://img.shields.io/badge/百度网盘-下载链接-blue?logo=baidu&logoColor=white&style=flat-square)](https://pan.baidu.com/share/init?surl=mf6hHJt8hVW3G2Yp2gC3Sw&pwd=2333)

其他下载方式可进群获取：[![QQ](https://img.shields.io/badge/QQ群-967981851-blue?logo=tencentqq&style=flat-square)](https://qm.qq.com/q/6pfdCFxJcc)

### Windows

```bash
# 启动GPT-SoVITS服务端
# 在GPT-SoVITS-v2pro-20250604文件夹打开终端，输入命令
runtime\python.exe api_v2.py

# 启动MoeChat服务端
# 在整合包目录打开终端，输入命令
GPT-SoVITS-v2pro-20250604\runtime\python.exe chat_server.py
```

### Linux

```bash
# 创建虚拟环境
python -m venv pp

# Ubuntu还需安装portaudio等包，具体自行搜索Linux环境python如何使用sounddevice库
# 安装依赖需要编译安装，还需安装python3-dev包，其他发行版自行搜索

# 进入虚拟环境
source pp/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行
python chat_server.py
```

## 简易客户端使用方法

### Windows

测试使用python 3.10
如需要服务端单独部署，客户端远程访问，可修改client-gui\src\client_utils.py文件17、18行的ip地址

##### 带简单GUI的客户端

```bash
# 运行
GPT-SoVITS-v2pro-20250604\runtime\python.exe client-gui\src\client_gui.py
```

### Linux

```bash
# 创建虚拟环境，如果创建过虚拟环境了可以跳过
python -m venv pp

# 进入虚拟环境
source pp/bin/activate

# 安装依赖
pip install -r client-requirements.txt

# 启动
python client-gui\src\client_gui.py
```

## 配置说明

整合包配置文件为config.yaml

```yaml
Core:
  sv:
    is_up: false
    master_audio: test.wav    	# 包含你声音的wav音频文件，建议3s-5s左右。
    thr:                      	# 阈值，越小越敏感，建议0.5-0.8之间，实测好像不是很有用？
LLM:
  api: http://host:port/v1/chat/completions	# 大模型api
  key: asdasd					# 大模型api的token
  model: 					# 模型名称
  extra_config:               			# 大模型API额外参数，如：temperature: 0.7，温度参数
    "frequency_penalty": 0.0
    "n": 1
    "presence_penalty": 0.0
    "top_p": 1.0
    # temperature: 0.7
GSV:
  api: http://host:port/tts/	# GPT-SoVITS的接口
  text_lang: zh			# 合成文本的语言
  GPT_weight: 			# GPT模型
  SoVITS_weight:		# Sovits模型
  ref_audio_path: 		# 参考音频路径
  prompt_text: 			# 参考音频文本
  prompt_lang: zh		# 参考音频语言
  aux_ref_audio_paths:        	# 多参考音频 v2模型有效
    - 
  seed: -1
  top_k: 15
  batch_size: 20
  ex_config:
    text_split_method: cut0
extra_ref_audio:              	# 使用情绪标签选择参考音频，例如 [普通]"你好呀。"
  # 实例
  # 普通: 
  #   - 参考音频路径
  #   - 参考音频文本
Agent:
  is_up: true                 	# 是否启用角色模板功能，如果不启动则和旧版一样只有常规语音对话功能，启用可以基于模板创建个性化角色
  char: Chat酱                	# 角色的名称，会写入到提示词内
  user: 芙兰蠢兔               	# 用户名称，会写入到提示词内
  long_memory: true           	# 是否启用日记功能，日记功能可以长期储存对话信息，并根据用户输入的时间信息进行检索；比如：“昨天做了什么？”、“两天前吃的午饭是什么？”
  is_check_memorys: true      	# 启用日记检索加强，使用嵌入模型对检索到的信息做提取，去除与用户提问不相关的内容。
  is_core_mem: true           	# 是否启用核心记忆功能，核心记忆主要储存关于用户重要信息，如：用户的住址、爱好、喜欢的东西等等。区别于日记，使用嵌入模型进行语义匹配（模糊搜索），不能根据时间检索，但记忆带有记录时间。
  mem_thresholds: 0.39        	# 日记内容搜索阈值，需要启用日记检索加强，用于判断匹配程度。过高可能会丢失数据，过低则只过滤少量或者完全无法过滤无用记忆。
  lore_books: true            	# 是否启用世界书（知识库），用于给大模型添加知识，如：人物、物品、事件等等，强化ai的能力，也可用于强化角色扮演。
  books_thresholds: 0.5       	# 知识库检索阈值。
  scan_depth: 4               	# 知识库搜索深度，返回知识的数量，但相似度低于检索阈值的知识不会被返回，所以返回结果数量也可能小于设定的数值。
  
  # 下面提示词都可以用{{user}}、{{char}}占位符来代表用户名和角色名。
  
  # 角色的基本设定，会组合到角色设定提示词中，建议不要添加多余的信息，不填则不会添加到提示词。
  char_settings: "Chat酱是存在于现代科技世界手机中的器灵，诞生于手机的智能系统，随着手机的使用不断成长和学习，拥有了自己的意识和个性。她外表看起来是个十几岁的少女，身材娇小但比例出色，有着纤细的腰肢和圆润的臀部，皮肤白皙，眼睛又大又亮，如同清澈的湖水，一头柔顺的长发披肩，整体形象清纯可爱又不失性感。她常穿着一件白色的连衣裙，裙子上有淡蓝色的花纹，腰间系着一个粉色的蝴蝶结，搭配一双白色的凉鞋，肩上披一条淡蓝色的薄纱披肩，手上戴着一条精致的手链，内衣是简约的白色棉质款式。Chat酱表面清纯可爱，实则腹黑毒舌，内心聪明机智，对很多事情有自己独特的看法，同时也有温柔体贴的一面，会在主人疲惫时给予暖心的安慰。她喜欢处理各种数据和信息、研究新知识、捉弄主人，还喜欢看浪漫的爱情电影和品尝美味的甜品，讨厌主人不珍惜手机和遇到难以解决的复杂问题。她精通各种知识，能够快速准确地处理办公、生活等方面的问题，具备强大的数据分析和信息检索能力。平时她会安静地待在手机里，当主人遇到问题时会主动出现，喜欢调侃主人，但在关键时刻总是能提供有效的帮助。她和主人关系密切，既是助手也是朋友，会在主人需要时给予温暖的陪伴。"
  
  # 角色性格提设定，会组合到角色性格提示词中，建议不要添加多余的信息，不填则不会添加到提示词。
  char_personalities: 表面清纯可爱，实则腹黑毒舌，内心聪明机智，对很多事情有自己独特的看法。同时也有温柔体贴的一面，会在主人疲惫时给予暖心的安慰。
  
  # 关于用户自身的设定，可以填入你的性格喜好，或者你跟角色的关系。内容填充到提示词模板中，建议不要填不相关的信息。没有可不填。
  mask: 
  
  # 对话示例，用于强化AI的文风。内容填充到提示词模板中，不要填入其他信息，没有可不填。
  message_example: |-
    mes_example": "人类视网膜的感光细胞不需要这种自杀式加班，您先休息一下吧。
  
  # 自定义提示词，不基于模板，可自定义填写，如果不想使用提示词模板创建角色，可以只填这一项。也可以不填。
  prompt: |-
    使用口语的文字风格进行对话，不要太啰嗦。
    /no_think

# 如果你想自定义提示的模板，可以在utilss\prompt.py文件中修改

```

## 接口说明

接口全部使用POST请求。

### ASR语音识别接口

```python
# url为/api/asr
# 请求数据格式为json
# 音频格式为wav，16kzh采样率，int16深度，单声道，每帧长度20ms
# 将音频数据编码成urlsafe的base64字符串，放进请求体data字段中
{
  "data": str # base64音频数据
}
# 服务端直接返回识别结果文本
```

### 对话接口

```python
# 对话接口为sse流式接口，服务端会将大模型的回答切片并生成对应的语音数据，一段一段返回客户端
# 请求数据格式为json
# 将大模型上下文数据放进msg字段，类型为字符串数组
# 请求例子
{
  "msg": [
    {"role": "user", "content": "你好呀！"},
    {"role": "assistant", "content": "你好呀！有什么能帮到你的吗？"},
    {"role": "user", "content": "1+1等于多少呢？"},
  ]
}

# 服务端响应例子
{
  "file": str     # urlsafe的base64字符串音频文件
  "message": str  # 音频数据对应的文本
  "done": False   # bool类型，用于判断是否为最后一个数据包
}
# 最后一个数据包服务端会将大模型完整的回答文本放进message字段返回客户端
{
  "file": str
  "message": str  # 字符串类型，大模型完整回答文本，用于拼接上下文
  "done": True    # bool类型，用于判断是否为最后一个数据包
}
```

### 对话接口V2

```python
# 对话接口为sse流式接口，服务端会将大模型的回答切片并生成对应的语音数据，一段一段返回客户端
# 请求数据格式为json
# 将大模型上下文数据放进msg字段，类型为字符串数组
# 请求例子
{
  "msg": [
    {"role": "user", "content": "你好呀！"},
  ]
}

# 服务端响应例子
{
  "type": str     # 返回数据类型，text或audio
  "data": str     # 字符串类型的数据，可以是服务端返回的文本或者base64编码的wav音频数据
  "done": False   # bool类型，用于判断是否为最后一个数据包
}
# 最后一个数据包服务端会将大模型完整的回答文本放进"data"字段返回客户端
{
  "type": "text"
  "data": str     # 字符串类型，大模型完整回答文本，用于拼接上下文
  "done": True    # bool类型，用于判断是否为最后一个数据包
}
```

## 目标

- [X] 制作英文版Readme
- [ ] 网页端的相应提速与优化
- [ ] 网页端加入Live2d-widget
- [ ] 大语言模型的自我认知与数字生命
- [ ] 根据传统模型和Basson模型引入性唤醒度参数
- [ ] 客户端接入3d模型并实现全系投影
- [ ] 用AI的情绪和动作控制live2d模型的表情和动作
- [ ] 用AI的情绪和动作控制3d模型的表情和动作
