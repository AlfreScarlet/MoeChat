from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
from modelscope import snapshot_download
import numpy as np
from utilss import log as Log

# def load_model():
#     model = SentenceTransformer("./utilss/models/Qwen3-Embedding-0.6B")
#     return model

# try:
#     embedding_model = load_model()
# except:
#     print(f"[错误]embedding模型为安装，开始安装embedding模型...")
#     model_id = "Qwen/Qwen3-Embedding-0.6B"
#     local_dir = "./utilss/models/Qwen3-Embedding-0.6B"
#     snapshot_download(model_id = model_id, local_dir=local_dir)
#     embedding_model = load_model()

# def t2vect(text: list[str]) -> np.ndarray[np.ndarray]:
#     return embedding_model.encode(text, prompt_name="query")
#     # print()

# 加载embedding模型
def load_model():
    return pipeline(
        Tasks.sentence_embedding,
        model="./utilss/models/nlp_gte_sentence-embedding_chinese-base",
        sequence_length=100
    )
try:
    embedding_model = load_model()
except:
    Log.logger.warning(f"embedding模型未安装，开始安装embedding模型...")
    model_id = "iic/nlp_gte_sentence-embedding_chinese-base"
    local_dir = "./utilss/models/nlp_gte_sentence-embedding_chinese-base"
    snapshot_download(model_id=model_id, cache_dir=local_dir)   # Using local_dir=local_dir caused problem on Linux.
    embedding_model = load_model()

def t2vect(text: list[str]) -> np.ndarray[np.ndarray]:
    return embedding_model(input={"source_sentence": text})["text_embedding"]

def test(msg: str, memorys: list, thresholds: float):
    input = {
        "source_sentence": [msg],
        "sentences_to_compare": memorys
    }
    scores = embedding_model(input=input)["scores"]
    res_msg = ""
    for i in range(len(scores)):
        if scores[i] > thresholds:
            res_msg += str(memorys[i]) + "\n\n"
    if res_msg:
        return res_msg
