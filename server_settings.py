import os


DEFAULT_WEB_HOST = "127.0.0.1"
DEFAULT_WEB_PORT = 8001
DEFAULT_SOCKET_PORT = 8002
DEFAULT_CORS_ORIGINS = (
    "http://127.0.0.1:8001",
    "http://localhost:8001",
)


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


def get_web_host() -> str:
    return os.getenv("MOECHAT_HOST", DEFAULT_WEB_HOST)


def get_web_port() -> int:
    return env_int("MOECHAT_PORT", DEFAULT_WEB_PORT)


def get_socket_host() -> str:
    return os.getenv("MOECHAT_SOCKET_HOST", get_web_host())


def get_socket_port() -> int:
    return env_int("MOECHAT_SOCKET_PORT", DEFAULT_SOCKET_PORT)


def get_cors_origins() -> list[str]:
    raw_origins = os.getenv("MOECHAT_CORS_ORIGINS")
    if raw_origins:
        return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    return list(DEFAULT_CORS_ORIGINS)


def cors_allows_credentials(origins: list[str]) -> bool:
    return "*" not in origins
