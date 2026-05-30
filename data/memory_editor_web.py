import json
import os
import sys
import traceback
from datetime import datetime, time
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for
from ruamel.yaml import YAML


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_AGENTS_DIR = DATA_DIR / "agents"
DEFAULT_AGENT_NAME = "Chat酱"
ALL_DATES_LABEL = "-- 所有日期 --"


def _env_path(name: str, default: Path) -> Path:
    value = os.environ.get(name, "").strip()
    return Path(value).expanduser().resolve() if value else default


def resolve_default_agent_name(agents_dir: Path | None = None) -> str:
    """Pick the same per-agent memory tree used by the main runtime."""
    agents_dir = agents_dir or _env_path("MOECHAT_MEMORY_EDITOR_AGENTS_DIR", DEFAULT_AGENTS_DIR)

    configured = os.environ.get("MOECHAT_MEMORY_EDITOR_AGENT", "").strip()
    if configured:
        return configured

    last_used_file = DATA_DIR / "last_used_agent.txt"
    if last_used_file.exists():
        last_used = last_used_file.read_text(encoding="utf-8").strip()
        if last_used:
            return last_used

    if (agents_dir / DEFAULT_AGENT_NAME / "info.yaml").is_file():
        return DEFAULT_AGENT_NAME

    for child in sorted(agents_dir.iterdir()) if agents_dir.exists() else []:
        if child.is_dir() and (child / "info.yaml").is_file():
            return child.name

    raise FileNotFoundError(f"未找到任何助手配置目录: {agents_dir}")


class MemoryEditor:
    """
    Offline editor for the runtime memory layout:
    data/agents/{agent}/core_mem.yml and data/agents/{agent}/memory/*.jsonl.
    """

    def __init__(self, agent_name: str | None = None, agents_dir: Path | None = None):
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.width = 4096
        self.db: list[dict] = []

        self.agents_dir = agents_dir or _env_path(
            "MOECHAT_MEMORY_EDITOR_AGENTS_DIR", DEFAULT_AGENTS_DIR
        )
        self.agent_name = agent_name or resolve_default_agent_name(self.agents_dir)
        self.agent_dir = (self.agents_dir / self.agent_name).resolve()
        self.core_mem_file = self.agent_dir / "core_mem.yml"
        self.long_mem_dir = self.agent_dir / "memory"

        self._validate_agent_dir()
        self.long_mem_dir.mkdir(parents=True, exist_ok=True)
        self.load_all_mems()

    def _validate_agent_dir(self) -> None:
        expected_root = self.agents_dir.resolve()
        if expected_root not in self.agent_dir.parents and self.agent_dir != expected_root:
            raise ValueError(f"助手目录越界: {self.agent_dir}")
        if not (self.agent_dir / "info.yaml").is_file():
            raise FileNotFoundError(
                f"助手配置不存在: {self.agent_dir / 'info.yaml'}。"
                "可用 MOECHAT_MEMORY_EDITOR_AGENT 指定要编辑的助手。"
            )

    def load_all_mems(self) -> None:
        """Load core and long memories from the selected assistant."""
        self.db.clear()
        error_count = 0
        try:
            error_count += self._load_core_mem()
            error_count += self._load_long_mem()
            self.db.sort(
                key=lambda item: (
                    self.get_datetime_from_entry(item) is None,
                    self.get_datetime_from_entry(item) or datetime.min,
                )
            )
            print(
                f"--- 已加载助手 {self.agent_name} 的 {len(self.db)} 条记忆，"
                f"加载过程中遇到 {error_count} 个警告。---"
            )
        except Exception as e:
            print(f"[严重错误] 加载记忆时发生错误: {e}")
            traceback.print_exc()
            self.db.clear()

    def _load_core_mem(self) -> int:
        warnings = 0
        if not self.core_mem_file.exists():
            print(f"[警告] 核心记忆文件未找到: {self.core_mem_file}")
            return warnings

        with self.core_mem_file.open("r", encoding="utf-8") as f:
            data = self.yaml.load(f) or {}

        if not isinstance(data, dict):
            print(f"[警告] 核心记忆文件不是字典结构: {self.core_mem_file}")
            return warnings + 1

        for uuid, entry in data.items():
            if isinstance(entry, dict) and "text" in entry and "time" in entry:
                self.db.append(
                    {
                        "type": "core",
                        "id": str(uuid),
                        "file": self.core_mem_file.name,
                        "data": entry,
                    }
                )
            elif isinstance(uuid, str) and uuid.startswith("#"):
                continue
            else:
                print(f"[警告] 跳过核心记忆中格式不正确的条目: ID={uuid}")
                warnings += 1
        return warnings

    def _load_long_mem(self) -> int:
        warnings = 0
        if not self.long_mem_dir.exists():
            print(f"[警告] 长期记忆目录未找到: {self.long_mem_dir}")
            return warnings

        for file_path in sorted(self.long_mem_dir.rglob("*.jsonl")):
            relative_file = file_path.relative_to(self.long_mem_dir).as_posix()
            try:
                with file_path.open("r", encoding="utf-8") as f:
                    for line_no, line in enumerate(f, start=1):
                        raw_line = line.strip()
                        if not raw_line:
                            continue
                        try:
                            data = json.loads(raw_line)
                        except json.JSONDecodeError as e:
                            print(
                                f"[警告] 跳过 {relative_file}:{line_no} 的无效 JSON: {e}"
                            )
                            warnings += 1
                            continue

                        if self._is_valid_long_memory(data):
                            timestamp = int(data["timestamp"])
                            self.db.append(
                                {
                                    "type": "long",
                                    "id": f"{relative_file}:{line_no}",
                                    "file": relative_file,
                                    "line_no": line_no,
                                    "data": data,
                                    "timestamp": timestamp,
                                }
                            )
                        else:
                            print(
                                f"[警告] 跳过长期记忆中格式不正确的条目: "
                                f"{relative_file}:{line_no}"
                            )
                            warnings += 1
            except Exception as e:
                print(f"[错误] 加载长期记忆 {relative_file} 失败: {e}")
                warnings += 1
        return warnings

    @staticmethod
    def _is_valid_long_memory(data: object) -> bool:
        if not isinstance(data, dict):
            return False
        if "timestamp" not in data or "msg" not in data or "text_tag" not in data:
            return False
        try:
            int(data["timestamp"])
        except (TypeError, ValueError):
            return False
        return True

    def get_datetime_from_entry(self, entry: dict):
        try:
            if entry.get("type") == "core":
                return datetime.strptime(entry["data"]["time"], "%Y-%m-%d %H:%M:%S")
            if entry.get("type") == "long":
                timestamp = entry.get("timestamp", entry["data"].get("timestamp"))
                return datetime.fromtimestamp(int(timestamp))
        except (ValueError, TypeError, KeyError, OSError):
            return None
        return None

    def get_unique_dates(self) -> list[str]:
        dates = set()
        for entry in self.db:
            dt = self.get_datetime_from_entry(entry)
            if dt:
                dates.add(dt.strftime("%Y-%m-%d"))
        return [ALL_DATES_LABEL] + sorted(dates)

    def find_entry_by_id_and_type(self, entry_id: str, entry_type: str):
        for entry in self.db:
            if entry.get("type") == entry_type and str(entry.get("id")) == str(entry_id):
                return entry
        return None

    def search(self, keyword, start_date_str, end_date_str):
        """Search tags, core memory text, and long-memory conversation content."""
        results = self.db
        kw_lower = keyword.lower() if keyword else None

        if kw_lower:
            filtered = []
            for entry in results:
                match = False
                if entry.get("type") == "core":
                    text = entry["data"].get("text", "").lower()
                    match = kw_lower in text
                elif entry.get("type") == "long":
                    msg = entry["data"].get("msg", "")
                    text_tag = entry["data"].get("text_tag", "").lower()
                    match = kw_lower in text_tag or kw_lower in msg.lower()
                if match:
                    filtered.append(entry)
            results = filtered

        start_dt, end_dt = None, None
        if start_date_str and start_date_str != ALL_DATES_LABEL:
            try:
                start_dt = datetime.combine(
                    datetime.strptime(start_date_str, "%Y-%m-%d"), time.min
                )
            except ValueError:
                pass
        if end_date_str and end_date_str != ALL_DATES_LABEL:
            try:
                end_dt = datetime.combine(
                    datetime.strptime(end_date_str, "%Y-%m-%d"), time.max
                )
            except ValueError:
                pass
        if start_dt or end_dt:
            results = [
                e
                for e in results
                if (dt := self.get_datetime_from_entry(e))
                and (not start_dt or dt >= start_dt)
                and (not end_dt or dt <= end_dt)
            ]
        return results

    def _save_yaml_data(self, file_path: Path, data: dict) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as f:
            self.yaml.dump(data, f)

    def _resolve_long_mem_file(self, filename: str) -> Path:
        file_path = (self.long_mem_dir / filename).resolve()
        root = self.long_mem_dir.resolve()
        if root not in file_path.parents and file_path != root:
            raise ValueError(f"长期记忆文件越界: {filename}")
        return file_path

    def save_entry(self, entry: dict) -> None:
        if entry.get("type") == "core":
            self._save_core_entry(entry)
        elif entry.get("type") == "long":
            self._rewrite_long_entry(entry, delete=False)
        else:
            raise ValueError("未知的条目类型")

    def delete_entry(self, entry: dict) -> None:
        if entry.get("type") == "core":
            self._delete_core_entry(entry)
        elif entry.get("type") == "long":
            self._rewrite_long_entry(entry, delete=True)
        else:
            raise ValueError("未知的条目类型")

    def _save_core_entry(self, entry: dict) -> None:
        data = {}
        if self.core_mem_file.exists():
            with self.core_mem_file.open("r", encoding="utf-8") as f:
                data = self.yaml.load(f) or {}
        if not isinstance(data, dict):
            raise ValueError(f"核心记忆文件不是字典结构: {self.core_mem_file}")
        data[entry["id"]] = entry["data"]
        self._save_yaml_data(self.core_mem_file, data)

    def _delete_core_entry(self, entry: dict) -> None:
        if not self.core_mem_file.exists():
            raise FileNotFoundError(f"核心记忆文件不存在: {self.core_mem_file}")
        with self.core_mem_file.open("r", encoding="utf-8") as f:
            data = self.yaml.load(f) or {}
        if entry["id"] in data:
            del data[entry["id"]]
            self._save_yaml_data(self.core_mem_file, data)
        else:
            raise KeyError(f"核心记忆条目不存在: {entry['id']}")

    def _rewrite_long_entry(self, entry: dict, delete: bool) -> None:
        filename = entry.get("file")
        if not filename:
            raise ValueError("长期记忆条目缺少文件名")

        file_path = self._resolve_long_mem_file(filename)
        if not file_path.exists():
            raise FileNotFoundError(f"长期记忆文件不存在: {file_path}")

        target_line_no = int(entry.get("line_no", 0))
        replaced = False
        output_lines: list[str] = []

        with file_path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                raw_line = line.strip()
                if not raw_line:
                    continue
                current = json.loads(raw_line)
                if line_no == target_line_no:
                    replaced = True
                    if not delete:
                        output_lines.append(
                            json.dumps(
                                entry["data"],
                                ensure_ascii=False,
                                separators=(",", ":"),
                            )
                        )
                    continue
                output_lines.append(
                    json.dumps(current, ensure_ascii=False, separators=(",", ":"))
                )

        if not replaced:
            raise KeyError(f"长期记忆条目不存在: {entry.get('id')}")

        with file_path.open("w", encoding="utf-8") as f:
            if output_lines:
                f.write("\n".join(output_lines) + "\n")
            else:
                f.write("")

    def refresh_long_memory_vector(self, updated_entry: dict, original_entry: dict) -> str | None:
        if updated_entry.get("type") != "long":
            return None

        old_tag = original_entry.get("data", {}).get("text_tag")
        new_tag = updated_entry.get("data", {}).get("text_tag")
        needs_refresh = old_tag != new_tag or "vector" not in updated_entry.get("data", {})
        if not needs_refresh:
            return None

        model_path = PROJECT_ROOT / "data" / "models" / "bge-base-zh-v1.5"
        if not model_path.exists():
            return "未找到本地 embedding 模型，已保留原 vector；增强检索可能仍按旧标签匹配。"

        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(str(model_path))
            vector = model.encode([new_tag], normalize_embeddings=True)[0]
            updated_entry["data"]["vector"] = (
                vector.tolist() if hasattr(vector, "tolist") else list(vector)
            )
        except Exception as e:
            return f"重新计算 vector 失败，已保留原 vector: {e}"

        return None


app = Flask(__name__)
app.secret_key = os.environ.get("MOECHAT_MEMORY_EDITOR_SECRET", os.urandom(24))
editor: MemoryEditor | None = None


def get_editor() -> MemoryEditor:
    global editor
    if editor is None:
        editor = MemoryEditor()
    return editor


@app.template_filter("strftime")
def _jinja2_filter_datetime(date, fmt=None):
    """Jinja2 filter for formatting dates/timestamps."""
    if date is None:
        return "N/A"
    if isinstance(date, (int, float)):
        try:
            date = datetime.fromtimestamp(date)
        except (OSError, ValueError):
            return "Invalid Timestamp"
    if isinstance(date, datetime):
        format_string = fmt if fmt else "%Y-%m-%d %H:%M:%S"
        try:
            return date.replace(tzinfo=None).strftime(format_string)
        except ValueError:
            return "Invalid Date Format"
    return str(date)


@app.context_processor
def inject_editor():
    return dict(editor=get_editor())


@app.route("/")
def index():
    active_editor = get_editor()
    results = []
    unique_dates = active_editor.get_unique_dates()
    return render_template("index.html", results=results, unique_dates=unique_dates)


@app.route("/search")
def search():
    active_editor = get_editor()
    keyword = request.args.get("keyword", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    try:
        results = active_editor.search(keyword, start_date, end_date)
        unique_dates = active_editor.get_unique_dates()

        for entry in results:
            if entry.get("type") == "long":
                entry["generated_preview"] = _generate_long_mem_preview(entry)

        flash(f"搜索到 {len(results)} 条结果。", "info")
    except Exception as e:
        flash(f"搜索时发生错误: {e}", "error")
        traceback.print_exc()
        results = []
        unique_dates = [ALL_DATES_LABEL]

    return render_template(
        "index.html",
        results=results,
        unique_dates=unique_dates,
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
    )


@app.route("/edit")
def edit_form():
    active_editor = get_editor()
    entry_id = request.args.get("id")
    entry_type = request.args.get("type")

    if not entry_id or not entry_type:
        flash("缺少条目 ID 或类型", "error")
        return redirect(url_for("index"))

    entry = active_editor.find_entry_by_id_and_type(entry_id, entry_type)
    if not entry:
        flash(f"未找到要编辑的条目 (ID: {entry_id}, 类型: {entry_type})", "error")
        return redirect(url_for("index"))

    return render_template("edit.html", entry=entry)


@app.route("/save", methods=["POST"])
def save_changes():
    active_editor = get_editor()
    try:
        entry_id_str = request.form["id"]
        entry_type = request.form["type"]
        original_entry = active_editor.find_entry_by_id_and_type(entry_id_str, entry_type)

        if not original_entry:
            raise KeyError(
                f"无法找到原始条目 (ID: {entry_id_str}, 类型: {entry_type}) 以进行保存"
            )

        updated_entry = {
            **original_entry,
            "data": dict(original_entry["data"]),
        }

        if entry_type == "core":
            updated_entry["data"]["text"] = request.form["text"]
        elif entry_type == "long":
            updated_entry["data"]["text_tag"] = request.form["text_tag"]
            updated_entry["data"]["msg"] = request.form["msg"]
            vector_warning = active_editor.refresh_long_memory_vector(
                updated_entry, original_entry
            )
        else:
            raise ValueError("未知的条目类型")

        active_editor.save_entry(updated_entry)
        active_editor.load_all_mems()
        if entry_type == "long" and vector_warning:
            flash(f"记忆保存成功；{vector_warning}", "warning")
        else:
            flash("记忆保存成功！", "success")

    except Exception as e:
        flash(f"保存记忆时出错: {e}", "error")
        traceback.print_exc()

    return redirect(url_for("index"))


@app.route("/delete", methods=["POST"])
def delete_item():
    active_editor = get_editor()
    try:
        entry_id_str = request.form["id"]
        entry_type = request.form["type"]

        entry_to_delete = active_editor.find_entry_by_id_and_type(
            entry_id_str, entry_type
        )
        if not entry_to_delete:
            raise KeyError(f"无法找到要删除的条目 (ID: {entry_id_str}, 类型: {entry_type})")

        active_editor.delete_entry(entry_to_delete)
        active_editor.load_all_mems()
        flash("记忆删除成功！", "success")

    except Exception as e:
        flash(f"删除记忆时出错: {e}", "error")
        traceback.print_exc()

    return redirect(url_for("index"))


def _generate_long_mem_preview(entry: dict) -> str:
    msg = entry.get("data", {}).get("msg", "")
    lines = msg.split("\n")

    preview_lines = []
    if len(lines) > 1:
        preview_lines.append(lines[1].strip())
    if len(lines) > 2:
        preview_lines.append(lines[2].strip())

    if not preview_lines and len(lines) > 1:
        preview_lines.append(lines[1].strip())
    return "\n\n".join(line for line in preview_lines if line)


if __name__ == "__main__":
    try:
        get_editor()
    except Exception as e:
        print(f"[严重] Flask 应用启动失败: {e}")
        traceback.print_exc()
        sys.exit(1)

    host = os.environ.get("MOECHAT_MEMORY_EDITOR_HOST", "127.0.0.1")
    port = int(os.environ.get("MOECHAT_MEMORY_EDITOR_PORT", "5051"))
    app.run(debug=True, host=host, port=port)
