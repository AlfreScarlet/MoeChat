"""
emotion_service.py - 情感服务主程序
职责：
1. 整合词库加载器和情感处理器
2. 提供统一的对外服务接口
3. 处理系统初始化和错误管理
4. 提供系统状态监控和统计信息
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from .keyword_loader import KeywordLoader
from .emotion_processor import EmotionProcessor

DEFAULT_CONFIG_PATH = Path(__file__).with_name("config.json")


class EmotionService:
    def __init__(self, config_path: str | os.PathLike | None = None):
        """
        初始化情感服务

        Args:
            config_path: 配置文件路径
        """
        self.config_path = str(config_path or DEFAULT_CONFIG_PATH)
        self.config = {}
        self.keyword_loader = None
        self.emotion_processor = None
        self.is_initialized = False

        # 统计信息
        self.stats = {
            "total_requests": 0,  # 总请求数
            "successful_responses": 0,  # 成功响应数
            "failed_responses": 0,  # 失败响应数
            "memes_sent": 0,  # 发送的表情包数量
            "emotion_stats": {},  # 各情感类别使用统计
            "last_error": None,  # 最后一次错误
        }

    def initialize(self) -> bool:
        """
        初始化情感服务系统

        Returns:
            bool: 初始化是否成功
        """
        print("[情感服务] 开始初始化系统...")

        try:
            # 1. 加载配置文件
            if not self._load_config():
                return False

            # 2. 初始化词库加载器
            print("[情感服务] 初始化词库加载器...")
            keywords_dir = self.config.get("paths", {}).get("keywords_dir", "./")
            self.keyword_loader = KeywordLoader(keywords_dir)

            if not self.keyword_loader.load_all_keywords():
                print("[情感服务] 词库加载失败")
                return False

            # 3. 初始化情感处理器
            print("[情感服务] 初始化情感处理器...")
            self.emotion_processor = EmotionProcessor(self.config_path)

            # 4. 验证表情包文件夹
            if not self._validate_meme_folders():
                print("[情感服务] 表情包文件夹验证失败")
                return False

            self.is_initialized = True
            print("[情感服务] 系统初始化完成")
            self._print_system_status()
            return True

        except Exception as e:
            print(f"[情感服务] 初始化失败：{e}")
            self.stats["last_error"] = str(e)
            return False

    def _load_config(self) -> bool:
        """加载配置文件"""
        try:
            if not os.path.exists(self.config_path):
                print(f"[情感服务] 配置文件 {self.config_path} 不存在")
                return False

            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)

            print(f"[情感服务] 配置文件加载成功")
            return True

        except Exception as e:
            print(f"[情感服务] 配置文件加载失败：{e}")
            return False

    def _validate_meme_folders(self) -> bool:
        """验证表情包文件夹是否存在"""
        try:
            memes_base_dir = self.config.get("paths", {}).get(
                "memes_base_dir", "memes/"
            )

            if not os.path.exists(memes_base_dir):
                print(f"[情感服务] 表情包基础目录 {memes_base_dir} 不存在")
                return False

            # 检查各情感文件夹
            emotions = self.keyword_loader.get_all_emotions()
            missing_folders = []
            empty_folders = []

            for emotion in emotions:
                folder_path = os.path.join(memes_base_dir, emotion)
                if not os.path.exists(folder_path):
                    missing_folders.append(emotion)
                else:
                    # 检查文件夹是否有图片文件
                    image_extensions = self.config.get("system_settings", {}).get(
                        "supported_image_formats",
                        [".png", ".jpg", ".jpeg", ".gif", ".webp"],
                    )

                    files = os.listdir(folder_path)
                    has_images = any(
                        any(f.lower().endswith(ext) for ext in image_extensions)
                        for f in files
                    )

                    if not has_images:
                        empty_folders.append(emotion)

            # 报告检查结果
            if missing_folders:
                print(f"[情感服务] 警告：缺少表情包文件夹：{missing_folders}")

            if empty_folders:
                print(f"[情感服务] 警告：以下文件夹为空：{empty_folders}")

            # 只要有部分文件夹可用就算验证通过
            available_folders = len(emotions) - len(missing_folders)
            print(
                f"[情感服务] 表情包文件夹验证完成：{available_folders}/{len(emotions)} 可用"
            )

            return available_folders > 0

        except Exception as e:
            print(f"[情感服务] 表情包文件夹验证失败：{e}")
            return False

    def _print_system_status(self):
        """打印系统状态信息"""
        print("\n" + "=" * 50)
        print("          情感表情包系统状态")
        print("=" * 50)

        # 词库状态
        if self.keyword_loader:
            stats = self.keyword_loader.get_statistics()
            print(f"词库状态: {stats.get('total_emotions', 0)} 个情感类别")
            print(f"关键词总数: {stats.get('total_keywords', 0)} 个")

        # 配置状态
        scoring_weights = self.config.get("scoring_weights", {})
        probability_config = self.config.get("probability_config", {})
        print(f"计分规则: {len(scoring_weights)} 项")
        print(
            f"概率设置: 主概率={probability_config.get('main_meme_probability', '未知')}, Default概率={probability_config.get('default_meme_probability', '未知')}"
        )

        # 调试模式
        debug_mode = self.config.get("system_settings", {}).get("debug_mode", False)
        print(f"调试模式: {'开启' if debug_mode else '关闭'}")

        print("=" * 50 + "\n")

    def process_llm_response(self, llm_response_text: str) -> Optional[str]:
        """
        处理LLM回复，生成表情包响应

        Args:
            llm_response_text: LLM的回复文本

        Returns:
            Optional[str]: SSE格式的表情包响应，None表示不发送表情包
        """
        if not self.is_initialized:
            print("[情感服务] 系统未初始化，尝试自动初始化...")
            if not self.initialize():
                print("[情感服务] 自动初始化失败")
                return None

        # 更新统计
        self.stats["total_requests"] += 1

        try:
            print(f"\n[情感服务] 处理请求 #{self.stats['total_requests']}")

            # 调用情感处理器
            sse_response = self.emotion_processor.process_emotion(llm_response_text)

            if sse_response:
                # 成功生成表情包响应
                self.stats["successful_responses"] += 1
                self.stats["memes_sent"] += 1

                # 提取情感类别用于统计
                try:
                    # 从SSE响应中提取情感文件夹名称
                    response_data = json.loads(sse_response.split("data: ")[1].strip())
                    message = response_data.get("message", "")
                    if "/memes/" in message:
                        emotion_folder = message.split("/memes/")[1].split("/")[0]
                        self.stats["emotion_stats"][emotion_folder] = (
                            self.stats["emotion_stats"].get(emotion_folder, 0) + 1
                        )
                except:
                    pass  # 统计提取失败不影响主流程

                print(f"[情感服务] 请求处理成功，发送表情包")
                return sse_response
            else:
                # 不发送表情包（概率未命中或其他原因）
                self.stats["successful_responses"] += 1
                print(f"[情感服务] 请求处理成功，但不发送表情包")
                return None

        except Exception as e:
            # 处理失败
            self.stats["failed_responses"] += 1
            self.stats["last_error"] = str(e)
            print(f"[情感服务] 请求处理失败：{e}")
            return None

    def get_system_statistics(self) -> Dict[str, Any]:
        """
        获取系统统计信息

        Returns:
            Dict: 系统统计信息
        """
        stats = self.stats.copy()

        # 添加词库统计
        if self.keyword_loader:
            keyword_stats = self.keyword_loader.get_statistics()
            stats["keyword_loader_stats"] = keyword_stats

        # 添加成功率计算
        if self.stats["total_requests"] > 0:
            stats["success_rate"] = (
                self.stats["successful_responses"] / self.stats["total_requests"]
            )
            stats["meme_send_rate"] = (
                self.stats["memes_sent"] / self.stats["total_requests"]
            )

        # 添加系统状态
        stats["system_initialized"] = self.is_initialized
        stats["config_loaded"] = bool(self.config)

        return stats

    def reload_system(self) -> bool:
        """
        重新加载整个系统（热更新）

        Returns:
            bool: 重新加载是否成功
        """
        print("[情感服务] 开始重新加载系统...")

        # 重置状态
        self.is_initialized = False

        # 重新初始化
        success = self.initialize()

        if success:
            print("[情感服务] 系统重新加载成功")
        else:
            print("[情感服务] 系统重新加载失败")

        return success

    def is_healthy(self) -> bool:
        """
        检查系统健康状态

        Returns:
            bool: 系统是否健康
        """
        return (
            self.is_initialized
            and self.keyword_loader is not None
            and self.emotion_processor is not None
            and self.keyword_loader.is_loaded
        )


# 全局服务实例（单例模式）
_emotion_service_instance = None


def get_emotion_service(config_path: str | os.PathLike | None = None) -> EmotionService:
    """
    获取情感服务实例（单例模式）

    Args:
        config_path: 配置文件路径

    Returns:
        EmotionService: 情感服务实例
    """
    global _emotion_service_instance
    if _emotion_service_instance is None:
        _emotion_service_instance = EmotionService(config_path)
    return _emotion_service_instance


if __name__ == "__main__":
    # 测试情感服务
    print("=" * 60)
    print("               情感表情包系统测试")
    print("=" * 60)

    # 创建服务实例
    service = EmotionService()

    # 初始化系统
    if service.initialize():
        print("\n开始测试LLM回复处理...")

        # 测试用例
        test_responses = [
            "哈哈，太好了！我很开心！",
            "唉，这真是太糟糕了...",
            "嗯？这个问题很奇怪啊？？？",
            "还行吧，没什么特别的感觉",
            "哇塞！这简直太棒了！！！",
        ]

        for i, response in enumerate(test_responses, 1):
            print(f"\n--- 测试 {i} ---")
            result = service.process_llm_response(response)
            if result:
                print(f"返回: {result.strip()}")
            else:
                print("返回: 无表情包")

        # 显示统计信息
        print("\n" + "=" * 60)
        print("                   系统统计")
        print("=" * 60)
        stats = service.get_system_statistics()
        print(f"总请求数: {stats['total_requests']}")
        print(f"成功响应: {stats['successful_responses']}")
        print(f"表情包发送: {stats['memes_sent']}")
        print(f"成功率: {stats.get('success_rate', 0):.2%}")
        print(f"表情包发送率: {stats.get('meme_send_rate', 0):.2%}")

        if stats.get("emotion_stats"):
            print("\n各情感类别使用统计:")
            for emotion, count in stats["emotion_stats"].items():
                print(f"  {emotion}: {count} 次")

    else:
        print("系统初始化失败！")
