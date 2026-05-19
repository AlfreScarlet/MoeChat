from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
long_mem = (ROOT / "utils" / "long_mem.py").read_text(encoding="utf-8")
agent = (ROOT / "utils" / "agent.py").read_text(encoding="utf-8")


def fail(message: str) -> None:
    raise SystemExit(message)


if "import pickle" in long_mem:
    fail("long_mem.py should not import unused pickle")
if "self._sort_loaded_memories()" not in long_mem:
    fail("long_mem.py must sort loaded memories before bisect lookup")
if "range(res_index[0] + 1" in long_mem:
    fail("long_mem.py still skips the first memory in a matched time range")
if "if self.enable_core_memory:" not in agent:
    fail("agent.py must honor enableCoreMemory before writing core memory")
if "if self.enable_long_memory:" not in agent:
    fail("agent.py must honor enableLongMemory before writing long memory")
