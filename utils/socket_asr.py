import socket
import threading
import struct
import json
from utils.pysilero import VADIterator
import numpy as np
import base64
from scipy.signal import resample
from io import BytesIO
import soundfile as sf
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess
from io import BytesIO
from utils.log import logger
from utils import config as CConfig
import httpx


class ASRServer:
    _instance = None
    _lock = threading.Lock()
    asr_model: AutoModel

    # 单例模式
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                # 双重检查锁定模式
                if cls._instance is None:
                    cls._instance = super(ASRServer, cls).__new__(cls)
        return cls._instance

    def load_model(self) -> None:
        """
        加载asr模型
        """
        if "ASR" in CConfig.config and CConfig.config["ASR"]["type"] == "api":
            logger.info("[提示]ASR使用API接口，无需加载本地模型。")
            return
        model_dir = "./data/models/SenseVoiceSmall"
        try:
            self.asr_model = AutoModel(
                model=model_dir,
                disable_update=True,
                device="cuda:0",
            )
        except Exception as e:
            logger.info(e)
            logger.info("[提示]未安装ASR模型，开始自动安装ASR模型。")
            from modelscope import snapshot_download

            model_dir = snapshot_download(
                model_id="iic/SenseVoiceSmall",
                local_dir=model_dir,
                revision="master",
            )
            model_dir = model_dir
            self.asr_model = AutoModel(
                model=model_dir,
                disable_update=True,
                # device="cuda:0",
                device="cpu",
            )

    def asr(self, audio_data: bytes) -> str | None:
        if "ASR" in CConfig.config and CConfig.config["ASR"]["type"] == "api":
            url = CConfig.config["ASR"]["api"]["url"]
            key = CConfig.config["ASR"]["api"]["key"]
            model = CConfig.config["ASR"]["api"]["model"]
            headers = {"Authorization": f"Bearer {key}"}
            base64_audio = base64.b64encode(audio_data).decode("utf-8")
            post_data = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "audio_url",
                                "audio_url": {
                                    "url": f"data:audio/wav;base64,{base64_audio}"
                                },
                            }
                        ],
                    }
                ],
            }
            try:
                response = httpx.post(url, json=post_data, headers=headers, timeout=5)
                response.raise_for_status()
                res_json = response.json()
                text = res_json["choices"][0]["message"]["content"]
                text = str(text).split("<asr_text>")[1]
                if text:
                    return text
            except Exception as e:
                logger.error(f"ASR API请求失败: {e}")
                return None
            return None

        # 从内存读取音频，转为 numpy 数组传给 FunASR（新版 torchaudio 不支持 BytesIO）
        audio_buffer = BytesIO(audio_data)
        data, samplerate = sf.read(audio_buffer, dtype="float32")
        res = self.asr_model.generate(
            input=data,
            cache={},
            language="zh",  # "zh", "en", "yue", "ja", "ko", "nospeech"
            ban_emo_unk=True,
            use_itn=False,
            disable_pbar=True,
            fs=samplerate,
            # batch_size=200,
        )
        text = str(rich_transcription_postprocess(res[0]["text"])).replace(" ", "")

        if text:
            return text
        return None