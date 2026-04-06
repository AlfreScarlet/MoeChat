# import
from models.types.assistant_info import AssistantInfo
from utils import embedding
from utils import log as Log
import yaml
import time
import faiss
import os
import shortuuid


os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


class CoreMemory:

    def __init__(self, agent_config: AssistantInfo):
        self.agent_id = agent_config.name
        self.char = agent_config.name
        self.user = agent_config.user
        self.thresholds = 0.31
        self.file_path = f"./data/agents/{self.agent_id}/core_mem.yml"
        # self.update_config()
        self.msgs = []
        self.mems = []
        self.uuid = []

        if os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                for key in data:
                    self.mems.append(data[key]["text"])
                    self.msgs.append(
                        f"记忆获取时间：{data[key]['time']}\n{data[key]['text']}"
                    )
                    self.uuid.append(key)
        else:
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write("\n\n# 核心记忆文件，请勿自行修改！否侧会丢失索引！\n\n")
            t_n = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
            uuid = shortuuid.ShortUUID().random(length=10)
            while uuid in self.uuid:
                uuid = shortuuid.ShortUUID().random(length=10)
            text = {uuid: {"time": t_n, "text": f"第一次相遇"}}
            with open(self.file_path, "a", encoding="utf-8") as f:
                yaml.safe_dump(text, f, allow_unicode=True)
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                for key in data:
                    self.mems.append(data[key]["text"])
                    self.msgs.append(
                        f"记忆获取时间：{data[key]['time']}\n{data[key]['text']}"
                    )
                    self.uuid.append(key)
        vects = embedding.t2vect(self.mems)
        self.index = faiss.IndexFlatIP(len(vects[0]))
        self.index.add(vects)

    def find_memories(self, msg: str, res_msg: list):
        """
        查找核心记忆
        Args:
            msg (str): 输入的消息
            res_msg (list): 输出的消息列表
        """
        D, I = self.index.search(embedding.t2vect([msg]), 5)
        msg = ""
        for index in range(len(D)):
            for i2 in range(len(D[index])):
                if D[index][i2] >= self.thresholds:
                    msg += self.msgs[I[index][i2]] + "\n"
        if msg:
            res_msg.append(msg)

    def add_memory(self, msg: list):
        m_list = {}
        for m in msg:
            uuid = shortuuid.ShortUUID().random(length=10)
            while uuid in self.uuid:
                uuid = shortuuid.ShortUUID().random(length=10)
            t_n = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
            m_list[uuid] = {"time": t_n, "text": m}
            self.mems.append(m)
            self.msgs.append(f"记忆获取时间：{t_n}\n{m}")
        with open(self.file_path, "a", encoding="utf-8") as f:
            yaml.safe_dump(m_list, f, allow_unicode=True)
        vects = embedding.t2vect(msg)
        self.index.add(vects)
        Log.logger.info(f"[提示]添加核心记忆{msg}")
