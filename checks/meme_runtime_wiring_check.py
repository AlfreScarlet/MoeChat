import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
chat_core = (ROOT / "core" / "chat_core.py").read_text(encoding="utf-8")
service = (ROOT / "core" / "meme_system" / "emotion_service.py").read_text(
    encoding="utf-8"
)
config = json.loads((ROOT / "core" / "meme_system" / "config.json").read_text())


def fail(message: str) -> None:
    raise SystemExit(message)


if "StreamProcessor(emotion_processed=True)" not in chat_core:
    fail("main chat stream must enable meme processing")
if "DEFAULT_CONFIG_PATH = Path(__file__).with_name(\"config.json\")" not in service:
    fail("meme service must resolve its default config relative to the module")

paths = config["paths"]
if paths["memes_base_dir"] != "web/resources/static/memes/":
    fail("memes_base_dir must point at the mounted static memes directory")
if paths["keywords_dir"] != "core/meme_system/":
    fail("keywords_dir must point at the checked-in keyword JSON files")
if paths["expression_url_prefix"] != "/memes/":
    fail("expression_url_prefix must match FastAPI's root static mount")

for path in (paths["memes_base_dir"], paths["keywords_dir"]):
    if not (ROOT / path).exists():
        fail(f"configured meme path does not exist: {path}")
