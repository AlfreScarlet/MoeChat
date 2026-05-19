from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
chat_api = (ROOT / "api" / "chat_api.py").read_text(encoding="utf-8")
agent = (ROOT / "utils" / "agent.py").read_text(encoding="utf-8")
frontend = (ROOT / "web" / "resources" / "static" / "js" / "moechat_core.js").read_text(
    encoding="utf-8"
)


def fail(message: str) -> None:
    raise SystemExit(message)


if '"/chat/context/clear"' not in chat_api:
    fail("chat_api.py must expose a backend context clear endpoint")
if "agent.clear_chat_context()" not in chat_api:
    fail("clear endpoint must clear the current assistant runtime context")
if "def clear_chat_context" not in agent:
    fail("Agent must implement clear_chat_context")
for required in ("self.msg_data = []", "self.msg_data_tmp = []", "history.yaml", "context_summary.md"):
    if required not in agent:
        fail(f"clear_chat_context is missing: {required}")
if "fetch('/api/chat/context/clear', { method: 'POST' })" not in frontend:
    fail("clear button must call the backend context clear endpoint")
if "清空聊天上下文失败" not in frontend:
    fail("clear failure must be visible in the UI")
