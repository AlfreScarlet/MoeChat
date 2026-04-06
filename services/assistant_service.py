import json
import os
import shutil
import time
from threading import Thread

import requests
import yaml
from Config import Config
from models.dto.assistant_request import AddAssistantRequest, UpdateAssistantRequest
from models.types.assistant_info import AssistantInfo
from utils.agent import Agent
from utils.file_utils import get_latest_modification_time
from utils import prompt
import utils.log as Log


class AssistantService:
    """
    助手服务类
    """

    _instance = None

    current_assistant: Agent | None = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 初始化当前助手为None
        self.current_assistant: Agent | None = None
        # 初始化当前助手名称为None
        self.current_assistant_name: str | None = None
        # 初始化助手信息缓存为空字典
        self.assistants_cache: dict[str, AssistantInfo] = {}
        # 初始化已加载助手为空字典
        self.loaded_agents: dict[str, Agent] = {}
        # 摘要总结线程
        self._summarize_thread: Thread | None = None

    def load_assistant_info(self) -> list[AssistantInfo]:
        """
        加载全部助手信息
        """
        assistants_path = Config.BASE_AGENTS_PATH
        assistants: list[AssistantInfo] = []

        # 确保路径存在
        if not os.path.exists(assistants_path):
            Log.logger.warning(f"助手路径不存在: {assistants_path}")
            raise FileNotFoundError(f"助手路径不存在: {assistants_path}")

        for dirname in os.listdir(assistants_path):
            file_path = os.path.join(assistants_path, dirname, "info.yaml")
            if os.path.isfile(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    assistant = yaml.safe_load(f)
                    # 添加最后修改时间信息，用于检查更新
                    assistant_dir = os.path.join(assistants_path, dirname)
                    assets_dir = os.path.join(assistant_dir, "assets")

                    # 获取最后修改时间
                    if os.path.exists(assets_dir):
                        # 获取assets目录下所有文件的最新修改时间
                        latest_mtime = get_latest_modification_time(assets_dir)
                        assistant["assetsLastModified"] = latest_mtime
                    else:
                        assistant["assetsLastModified"] = 0

                    assistant_info = AssistantInfo.from_dict(assistant)

                    assistants.append(assistant)
                    # 缓存助手信息
                    self.assistants_cache[assistant_info.name] = assistant_info
        return assistants

    def update_assistant_info(
        self, update_request: UpdateAssistantRequest
    ) -> AssistantInfo:
        """
        更新助手信息
        """
        assistants_path = Config.BASE_AGENTS_PATH
        # 使用助手名称作为目录名
        assistant_dir = os.path.join(assistants_path, update_request.name)
        info_file_path = os.path.join(assistant_dir, "info.yaml")

        # 检查助手是否存在
        if not os.path.exists(assistant_dir) or not os.path.isfile(info_file_path):
            raise FileNotFoundError(f"助手 '{update_request.name}' 不存在")

        # 读取现有信息
        with open(info_file_path, "r", encoding="utf-8") as f:
            existing_info = yaml.safe_load(f)

        # 更新信息（只更新非None字段）
        update_data = update_request.model_dump(exclude_unset=True)
        existing_info.update(update_data)

        # 更新时间戳
        existing_info["updatedAt"] = int(time.time())

        # 获取assets最后修改时间
        assets_dir = os.path.join(assistant_dir, "assets")

        if os.path.exists(assets_dir):
            existing_info["assetsLastModified"] = get_latest_modification_time(
                assets_dir
            )
        else:
            existing_info["assetsLastModified"] = 0

        # 保存更新后的信息
        with open(info_file_path, "w", encoding="utf-8") as f:
            yaml.dump(existing_info, f, allow_unicode=True, default_flow_style=False)

        # 更新缓存
        assistant_info = AssistantInfo.from_dict(existing_info)
        self.assistants_cache[assistant_info.name] = assistant_info

        # 如果当前正在使用的助手被更新，重新加载
        if self.current_assistant_name == update_request.name:
            self.reload_current_assistant()

        return assistant_info

    def add_assistant(self, add_request: AddAssistantRequest) -> AssistantInfo:
        """
        添加新助手
        """
        assistants_path = Config.BASE_AGENTS_PATH
        # 使用助手名称作为目录名
        assistant_dir = os.path.join(assistants_path, add_request.name)
        info_file_path = os.path.join(assistant_dir, "info.yaml")

        if not add_request.name:
            raise ValueError("助手名称不能为空")

        # 检查助手是否已存在
        if os.path.exists(assistant_dir):
            raise ValueError(f"助手 '{add_request.name}' 已存在")

        # 创建助手目录和必要的子目录
        os.makedirs(assistant_dir, exist_ok=True)
        os.makedirs(os.path.join(assistant_dir, "assets"), exist_ok=True)
        os.makedirs(os.path.join(assistant_dir, "memory"), exist_ok=True)
        os.makedirs(os.path.join(assistant_dir, "data_base"), exist_ok=True)

        special_settings = {
            "firstMeetTime": int(time.time()),
            "love": 0,
            "updatedAt": int(time.time()),
            "assetsLastModified": 0,
        }
        # 创建基本助手信息
        assistant_info = {
            **add_request.model_dump(),
            **special_settings,
        }

        # 保存助手信息
        with open(info_file_path, "w", encoding="utf-8") as f:
            yaml.dump(assistant_info, f, allow_unicode=True, default_flow_style=False)

        # 更新缓存
        assistant_info_obj = AssistantInfo.from_dict(assistant_info)
        self.assistants_cache[assistant_info_obj.name] = assistant_info_obj

        return assistant_info_obj

    def delete_assistant(self, assistant_name: str) -> None:
        """
        删除助手
        """
        assistants_path = Config.BASE_AGENTS_PATH
        # 使用助手名称作为目录名
        assistant_dir = os.path.join(assistants_path, assistant_name)

        # 检查助手是否存在
        if not os.path.exists(assistant_dir):
            raise FileNotFoundError(f"助手 '{assistant_name}' 不存在")

        # 如果当前正在使用该助手，先释放
        if self.current_assistant_name == assistant_name:
            self.current_assistant = None
            self.current_assistant_name = None

        # 从缓存中移除
        if assistant_name in self.assistants_cache:
            del self.assistants_cache[assistant_name]
        if assistant_name in self.loaded_agents:
            del self.loaded_agents[assistant_name]

        # 删除助手目录及其所有内容
        shutil.rmtree(assistant_dir)

    def set_assistant(self, assistant_name: str) -> Agent:
        """
        设置当前助手

        Args:
            assistant_name: 助手名称

        Returns:
            Agent实例

        Raises:
            FileNotFoundError: 当助手不存在时
        """
        # 检查助手配置文件是否存在
        assistant_info_path = os.path.join(
            Config.BASE_AGENTS_PATH, assistant_name, "info.yaml"
        )
        if not os.path.exists(assistant_info_path):
            raise FileNotFoundError(f"助手 '{assistant_name}' 不存在")

        # 检查助手是否已经加载
        if assistant_name in self.loaded_agents:
            self.current_assistant = self.loaded_agents[assistant_name]
            self.current_assistant_name = assistant_name
            Log.logger.info(f"已切换到助手: {assistant_name}")
            return self.current_assistant

        # 尝试创建新的Agent实例
        try:
            agent = Agent(assistant_name)
            self.current_assistant = agent
            self.current_assistant_name = assistant_name
            self.loaded_agents[assistant_name] = agent
            self._start_summarize_thread()
            Log.logger.info(f"已加载并切换到助手: {assistant_name}")
            return agent
        except Exception as e:
            Log.logger.error(f"加载助手失败: {assistant_name}, 错误: {e}")
            raise FileNotFoundError(f"加载助手 '{assistant_name}' 失败: {str(e)}")

    def get_current_assistant(self) -> Agent | None:
        """
        获取当前助手

        Returns:
            当前助手实例或None
        """
        return self.current_assistant

    def get_current_assistant_name(self) -> str | None:
        """
        获取当前使用的助手名称

        Returns:
            当前助手名称或None
        """
        return self.current_assistant_name

    def reload_current_assistant(self) -> None:
        """
        重新加载当前助手
        """
        if self.current_assistant_name:
            try:
                # 创建新的Agent实例
                agent = Agent(self.current_assistant_name)
                self.current_assistant = agent
                self.loaded_agents[self.current_assistant_name] = agent
                Log.logger.info(f"已重新加载助手: {self.current_assistant_name}")
            except Exception as e:
                Log.logger.error(
                    f"重新加载助手失败: {self.current_assistant_name}, 错误: {e}"
                )
                raise FileNotFoundError(
                    f"重新加载助手 '{self.current_assistant_name}' 失败: {str(e)}"
                )

    def initialize_default_assistant(self) -> Agent | None:
        """
        初始化默认助手
        1. 尝试加载上次使用的助手
        2. 如果没有，尝试加载'Chat酱'
        3. 如果都没有，返回None
        """
        # 尝试获取上次使用的助手
        last_used_file = os.path.join(Config.BASE_DATA_PATH, "last_used_agent.txt")

        last_used = None

        if os.path.exists(last_used_file):
            try:
                with open(last_used_file, "r", encoding="utf-8") as f:
                    last_used = f.read().strip()
            except Exception as e:
                Log.logger.error(f"读取上次使用的助手失败: {e}")

        # 尝试加载上次使用的助手
        if last_used:
            try:
                return self.set_assistant(last_used)
            except:
                Log.logger.info(f"无法加载上次使用的助手: {last_used}")

        # 尝试加载默认助手'Chat酱'
        try:
            return self.set_assistant("Chat酱")
        except:
            Log.logger.info("无法加载默认助手'Chat酱'")
        return None

    def save_last_used_agent(self) -> None:
        """
        保存当前使用的助手名称，以便下次启动时自动加载
        """
        if self.current_assistant_name:
            try:
                last_used_file = os.path.join(
                    Config.BASE_DATA_PATH, "last_used_agent.txt"
                )
                with open(last_used_file, "w", encoding="utf-8") as f:
                    f.write(self.current_assistant_name)
                Log.logger.info(f"已保存最后使用的助手: {self.current_assistant_name}")
            except Exception as e:
                Log.logger.error(f"保存最后使用的助手失败: {e}")

    def get_assistant_by_name(self, assistant_name: str) -> AssistantInfo | None:
        """
        根据名称获取助手信息

        Args:
            assistant_name: 助手名称

        Returns:
            助手信息或None
        """
        # 先从缓存中查找
        if assistant_name in self.assistants_cache:
            return self.assistants_cache[assistant_name]

        # 如果缓存中没有，尝试加载
        file_path = os.path.join(Config.BASE_AGENTS_PATH, assistant_name, "info.yaml")

        if os.path.isfile(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    assistant = yaml.safe_load(f)
                    # 添加最后修改时间信息
                    assistant_dir = os.path.join(
                        Config.BASE_AGENTS_PATH, assistant_name
                    )
                    assets_dir = os.path.join(assistant_dir, "assets")

                    if os.path.exists(assets_dir):
                        assistant["assetsLastModified"] = get_latest_modification_time(
                            assets_dir
                        )
                    else:
                        assistant["assetsLastModified"] = 0

                    assistant_info = AssistantInfo.from_dict(assistant)
                    self.assistants_cache[assistant_name] = assistant_info
                    return assistant_info
            except Exception as e:
                Log.logger.error(f"加载助手信息失败: {assistant_name}, 错误: {e}")

        return None

    def _start_summarize_thread(self) -> None:
        """
        启动摘要总结线程，遍历所有已加载助手进行摘要检查。
        仅在线程未运行时启动。
        """
        if self._summarize_thread is not None and self._summarize_thread.is_alive():
            return
        self._summarize_thread = Thread(
            target=self._summarize_context_loop, args=(), daemon=True
        )
        self._summarize_thread.start()

    def _summarize_context_loop(self) -> None:
        """
        摘要总结循环，定期遍历所有已加载助手，检查是否需要摘要总结
        """
        while True:
            time.sleep(300)
            for agent in list(self.loaded_agents.values()):
                try:
                    if (
                        time.time() + 3600 > agent.summary_time
                        and len(agent.msg_data)
                        > agent.agent_config.settings.contextLength
                    ):
                        self._do_summarize(agent)
                except Exception as e:
                    Log.logger.error(
                        f"助手 {agent.agent_name} 摘要检查异常：{e}"
                    )

    def _do_summarize(self, agent: Agent) -> None:
        """
        对指定助手执行一次摘要总结
        """
        Log.logger.info("开始总结摘要...")
        context = ""
        for msg in agent.msg_data:
            if msg["role"] == "user":
                context += f"{agent.user}：{msg['content']}\n"
                continue
            if msg["role"] == "assistant":
                context += f"{agent.char}：{msg['content']}\n\n"
                continue
        user_prompy = (
            prompt.context_summary
            .replace("{{char}}", agent.char)
            .replace("{{user}}", agent.user)
            .replace("{{context}}", context)
        )
        if agent.context_summary:
            user_prompy = user_prompy.replace(
                "{{old_context_summary}}", agent.context_summary
            )
        else:
            user_prompy = user_prompy.replace("{{old_context_summary}}", "无")
        res_body = {
            "model": agent.llm_config["model"],
            "messages": [
                {"role": "user", "content": user_prompy},
            ],
        }
        key = agent.llm_config["key"]
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        try:
            res = requests.post(
                agent.llm_config["api"],
                json=res_body,
                headers=headers,
                timeout=120,
            )
            res_context_summary = res.json()["choices"][0]["message"]["content"]

            # 存入文件
            with open(
                f"./data/agents/{agent.agent_name}/context_summary.md",
                "w",
                encoding="utf-8",
            ) as f:
                f.write(res_context_summary)
            with open(
                f"./data/agents/{agent.agent_name}/history.yaml",
                "w",
                encoding="utf-8",
            ) as f:
                pass

            # 写入agent变量，清空聊天列表
            agent.context_summary = res_context_summary
            agent.msg_data = []
        except Exception as e:
            Log.logger.error(f"摘要失败：{e}")
            return

        Log.logger.info("摘要总结完毕...")
