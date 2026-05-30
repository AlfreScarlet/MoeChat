from pathlib import Path


RUNTIME_PATHS = [
    "api",
    "core",
    "utils",
    "web",
    "services",
    "init_server.py",
    "main_web.py",
]


def assert_financial_config_disabled(repo_root: Path) -> None:
    config = (repo_root / "plugins" / "financial" / "config.yml").read_text(
        encoding="utf-8"
    )
    assert "enabled: false" in config
    assert "enabled: true" not in config


def assert_balancer_localhost_default(repo_root: Path) -> None:
    app_py = (repo_root / "plugins" / "financial" / "balancer" / "app.py").read_text(
        encoding="utf-8"
    )
    assert 'MOECHAT_FINANCIAL_HOST", "127.0.0.1"' in app_py
    assert 'MOECHAT_FINANCIAL_PORT", "5000"' in app_py
    assert 'app.run(host="0.0.0.0", port=5000' not in app_py


def assert_main_runtime_does_not_claim_hook(repo_root: Path) -> None:
    hits = []
    for rel_path in RUNTIME_PATHS:
        path = repo_root / rel_path
        files = [path] if path.is_file() else path.rglob("*.py")
        for file_path in files:
            text = file_path.read_text(encoding="utf-8")
            if "financial_plugin_hook" in text or "plugins.financial" in text:
                hits.append(str(file_path.relative_to(repo_root)))
    assert not hits, f"unexpected main-runtime financial hook references: {hits}"


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    assert_financial_config_disabled(repo_root)
    assert_balancer_localhost_default(repo_root)
    assert_main_runtime_does_not_claim_hook(repo_root)
    print("financial plugin standalone check passed")


if __name__ == "__main__":
    main()
