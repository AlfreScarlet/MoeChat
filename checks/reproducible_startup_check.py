import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    raise SystemExit(message)


readme = (ROOT / "README.md").read_text(encoding="utf-8")
gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
config = (ROOT / "config.yaml").read_text(encoding="utf-8")
pyproject_text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
pyproject = tomllib.loads(pyproject_text)

if "chat_server.py" in readme:
    fail("README still points users at missing chat_server.py")
if "3.10" in readme or "moechat310" in readme:
    fail("README still documents Python 3.10 while pyproject requires 3.11+")
if re.search(r"^test\*", gitignore, re.MULTILINE):
    fail(".gitignore still blocks adding test files")
if re.search(r"^uv\.lock$", gitignore, re.MULTILINE):
    fail(".gitignore still blocks committing uv.lock")
if re.search(r"sk-[A-Za-z0-9]{12,}", config):
    fail("config.yaml still contains an API-key-shaped secret")
if "sys_platform != 'linux'" in pyproject_text:
    fail("PyTorch source marker still routes non-Linux platforms to Windows CUDA")

dependencies = "\n".join(pyproject["project"]["dependencies"])
for required in ("requests", "pyyaml", "jinja2", "filetype"):
    if required not in dependencies.lower():
        fail(f"pyproject.toml is missing direct dependency: {required}")

if pyproject["project"]["requires-python"] != ">=3.11":
    fail("Unexpected Python version requirement")
