import importlib.util
import json
import sys
import tempfile
import types
from pathlib import Path


def install_fake_flask() -> None:
    fake_flask = types.ModuleType("flask")

    class FakeFlask:
        def __init__(self, *args, **kwargs):
            self.secret_key = None

        def template_filter(self, *args, **kwargs):
            return lambda fn: fn

        def context_processor(self, fn):
            return fn

        def route(self, *args, **kwargs):
            return lambda fn: fn

        def run(self, *args, **kwargs):
            return None

    fake_flask.Flask = FakeFlask
    fake_flask.flash = lambda *args, **kwargs: None
    fake_flask.redirect = lambda target: target
    fake_flask.render_template = lambda *args, **kwargs: ""
    fake_flask.request = types.SimpleNamespace(args={}, form={})
    fake_flask.url_for = lambda endpoint, *args, **kwargs: endpoint
    sys.modules["flask"] = fake_flask


def install_fake_ruamel() -> None:
    fake_ruamel = types.ModuleType("ruamel")
    fake_yaml_module = types.ModuleType("ruamel.yaml")

    class FakeYAML:
        preserve_quotes = True
        width = 4096

        def load(self, stream):
            text = stream.read()
            data = {}
            current_key = None
            for raw_line in text.splitlines():
                if not raw_line.strip() or raw_line.lstrip().startswith("#"):
                    continue
                if not raw_line.startswith(" ") and raw_line.endswith(":"):
                    current_key = raw_line[:-1]
                    data[current_key] = {}
                    continue
                if current_key and raw_line.startswith("  ") and ":" in raw_line:
                    key, value = raw_line.strip().split(":", 1)
                    data[current_key][key] = value.strip().strip("'\"")
            return data

        def dump(self, data, stream):
            for key, value in data.items():
                stream.write(f"{key}:\n")
                for child_key, child_value in value.items():
                    stream.write(f"  {child_key}: {child_value}\n")

    fake_yaml_module.YAML = FakeYAML
    sys.modules["ruamel"] = fake_ruamel
    sys.modules["ruamel.yaml"] = fake_yaml_module


def load_memory_editor(repo_root: Path):
    install_fake_flask()
    install_fake_ruamel()
    module_path = repo_root / "data" / "memory_editor_web.py"
    spec = importlib.util.spec_from_file_location("memory_editor_web_check", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = load_memory_editor(repo_root)

    with tempfile.TemporaryDirectory() as tmp:
        agents_dir = Path(tmp) / "agents"
        agent_dir = agents_dir / "TestAgent"
        memory_dir = agent_dir / "memory"
        memory_dir.mkdir(parents=True)
        (agent_dir / "info.yaml").write_text("name: TestAgent\n", encoding="utf-8")
        (agent_dir / "core_mem.yml").write_text(
            "abc123:\n  time: '2026-05-19 10:00:00'\n  text: 原始核心记忆\n",
            encoding="utf-8",
        )
        long_entry = {
            "timestamp": 1779184800,
            "text_tag": "原始标签",
            "msg": "时间：2026-05-19 10:00:00\n{{user}}：今天吃了苹果\n{{char}}：记住了",
            "vector": [0.1, 0.2],
        }
        (memory_dir / "2026-5-19.jsonl").write_text(
            json.dumps(long_entry, ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

        editor = module.MemoryEditor(agent_name="TestAgent", agents_dir=agents_dir)
        assert len(editor.db) == 2
        assert len(editor.search("苹果", "", "")) == 1
        assert editor.search("", "2026-05-19", "2026-05-19")

        long_item = next(item for item in editor.db if item["type"] == "long")
        updated = {**long_item, "data": dict(long_item["data"])}
        updated["data"]["text_tag"] = "更新标签"
        updated["data"]["msg"] = "时间：2026-05-19 10:00:00\n{{user}}：今天吃了梨\n{{char}}：记住了"
        warning = editor.refresh_long_memory_vector(updated, long_item)
        assert warning and "保留原 vector" in warning
        editor.save_entry(updated)

        saved_line = (memory_dir / "2026-5-19.jsonl").read_text(encoding="utf-8").strip()
        saved = json.loads(saved_line)
        assert saved["text_tag"] == "更新标签"
        assert saved["vector"] == [0.1, 0.2]
        assert "梨" in saved["msg"]

        editor.load_all_mems()
        long_item = next(item for item in editor.db if item["type"] == "long")
        editor.delete_entry(long_item)
        assert (memory_dir / "2026-5-19.jsonl").read_text(encoding="utf-8") == ""

    print("memory editor runtime schema check passed")


if __name__ == "__main__":
    main()
