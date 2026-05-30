from pathlib import Path


def assert_external_router_unmounted(repo_root: Path) -> None:
    router = (repo_root / "web" / "src" / "router" / "router.py").read_text(
        encoding="utf-8"
    )
    assert "# from core.external_server import router as models_router" in router
    assert "# app.include_router(models_router, prefix=\"/web\")" in router
    assert "app.include_router(models_router, prefix=\"/web\")" not in router.replace(
        "# app.include_router(models_router, prefix=\"/web\")", ""
    )


def assert_main_chat_has_no_weather_hook(repo_root: Path) -> None:
    chat_core = (repo_root / "core" / "chat_core.py").read_text(encoding="utf-8")
    assert "HeWeather" not in chat_core
    assert "get_heweather_dynamic" not in chat_core
    assert "weather_fetcher" not in chat_core


def assert_weather_docs_mark_standalone(repo_root: Path) -> None:
    readme = (repo_root / "weather" / "README.md").read_text(encoding="utf-8")
    assert "standalone experimental CLI" in readme
    assert "not" in readme and "main web chat path" in readme


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    assert_external_router_unmounted(repo_root)
    assert_main_chat_has_no_weather_hook(repo_root)
    assert_weather_docs_mark_standalone(repo_root)
    print("weather standalone status check passed")


if __name__ == "__main__":
    main()
