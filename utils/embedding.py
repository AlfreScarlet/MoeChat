from sentence_transformers import SentenceTransformer
import numpy as np
from utils import log as Log

if None:
    import os
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

model_path = "./data/models/bge-base-zh-v1.5"
QUERY_INSTRUCTION = "为这个句子生成表示以用于检索相关记忆段落："

# 加载embedding模型
def load_model():
    return SentenceTransformer(model_path)

try:
    embedding_model = load_model()
except:
    Log.logger.warning(f"embedding模型未安装，开始安装embedding模型...")
    model = SentenceTransformer("BAAI/bge-base-zh-v1.5")
    model.save(model_path)
    embedding_model = load_model()


# 存储用 —— 不加前缀
def t2vect(text: list[str]) -> np.ndarray[np.ndarray]:
    return embedding_model.encode(text, normalize_embeddings=True)


# 检索用 —— 加前缀
def q2vect(text: list[str]) -> np.ndarray[np.ndarray]:
    return embedding_model.encode(
        [QUERY_INSTRUCTION + t for t in text], 
        normalize_embeddings=True
    )


def test(msg: str, memorys: list, thresholds: float):
    input = {"source_sentence": [msg], "sentences_to_compare": memorys}
    scores = embedding_model(input=input)["scores"]
    res_msg = ""
    for i in range(len(scores)):
        if scores[i] > thresholds:
            res_msg += str(memorys[i]) + "\n\n"
    if res_msg:
        return res_msg
