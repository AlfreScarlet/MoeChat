import io
import os
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath, PureWindowsPath
from uuid import uuid4

from Config import Config


MAX_ASSISTANT_NAME_LENGTH = 128
MAX_ASSETS_ZIP_BYTES = 256 * 1024 * 1024
MAX_ASSETS_TOTAL_BYTES = 512 * 1024 * 1024
MAX_ASSET_FILE_BYTES = 128 * 1024 * 1024
MAX_ASSET_FILE_COUNT = 5000


class AssistantPathError(ValueError):
    """Raised when an assistant name or derived path escapes data/agents."""


class AssistantAssetsZipError(ValueError):
    """Raised when an uploaded assets zip is unsafe or malformed."""


def agents_root() -> Path:
    return Path(Config.BASE_AGENTS_PATH).resolve()


def validate_assistant_name(name: str) -> str:
    if not isinstance(name, str):
        raise AssistantPathError("Assistant name must be a string")
    if not name or name != name.strip():
        raise AssistantPathError("Assistant name cannot be empty or padded")
    if len(name) > MAX_ASSISTANT_NAME_LENGTH:
        raise AssistantPathError("Assistant name is too long")
    if "\x00" in name or any(ord(char) < 32 for char in name):
        raise AssistantPathError("Assistant name contains control characters")
    if "/" in name or "\\" in name:
        raise AssistantPathError("Assistant name cannot contain path separators")
    if name in {".", ".."}:
        raise AssistantPathError("Assistant name cannot be a relative path segment")
    if Path(name).is_absolute() or PureWindowsPath(name).is_absolute():
        raise AssistantPathError("Assistant name cannot be an absolute path")
    return name


def _ensure_under_root(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise AssistantPathError(f"Resolved path escapes assistants root: {path}") from exc
    return resolved


def resolve_assistant_dir(name: str, *, must_exist: bool = False) -> Path:
    safe_name = validate_assistant_name(name)
    root = agents_root()
    assistant_dir = _ensure_under_root(root / safe_name, root)
    if must_exist and not assistant_dir.is_dir():
        raise FileNotFoundError(f"Assistant '{safe_name}' not found")
    return assistant_dir


def resolve_assistant_file(
    name: str, *relative_parts: str, must_exist: bool = False
) -> Path:
    assistant_dir = resolve_assistant_dir(name, must_exist=True)
    target = _ensure_under_root(assistant_dir.joinpath(*relative_parts), assistant_dir)
    if must_exist and not target.is_file():
        raise FileNotFoundError(f"Assistant file not found: {target.name}")
    return target


def _is_zip_symlink(info: zipfile.ZipInfo) -> bool:
    return ((info.external_attr >> 16) & 0o170000) == 0o120000


def _remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def _normalise_asset_member(
    info: zipfile.ZipInfo, *, has_assets_dir: bool, assets_dir: Path
) -> tuple[zipfile.ZipInfo, Path] | None:
    filename = info.filename
    if not filename or "\x00" in filename or "\\" in filename:
        raise AssistantAssetsZipError(f"Unsafe zip member name: {filename!r}")
    if PureWindowsPath(filename).is_absolute():
        raise AssistantAssetsZipError(f"Absolute zip member is not allowed: {filename}")
    if _is_zip_symlink(info):
        raise AssistantAssetsZipError(f"Symlink zip member is not allowed: {filename}")

    member_path = PurePosixPath(filename)
    if member_path.is_absolute() or any(part in {"", ".", ".."} for part in member_path.parts):
        raise AssistantAssetsZipError(f"Path traversal zip member is not allowed: {filename}")

    if has_assets_dir:
        if not member_path.parts or member_path.parts[0] != "assets":
            return None
        relative_parts = member_path.parts[1:]
    else:
        relative_parts = member_path.parts

    if not relative_parts:
        return None

    target = assets_dir.joinpath(*relative_parts).resolve()
    try:
        target.relative_to(assets_dir.resolve())
    except ValueError as exc:
        raise AssistantAssetsZipError(f"Zip member escapes assets directory: {filename}") from exc
    return info, target


def replace_assets_from_zip(name: str, zip_content: bytes) -> Path:
    if len(zip_content) > MAX_ASSETS_ZIP_BYTES:
        raise AssistantAssetsZipError("Uploaded zip is too large")

    assistant_dir = resolve_assistant_dir(name, must_exist=True)
    assets_dir = assistant_dir / "assets"
    temp_root = Path(
        tempfile.mkdtemp(prefix=".assets-upload-", dir=str(assistant_dir))
    ).resolve()
    temp_assets_dir = temp_root / "assets"
    temp_assets_dir.mkdir()
    backup_dir = assistant_dir / f".assets-backup-{uuid4().hex}"
    moved_existing = False

    try:
        with zipfile.ZipFile(io.BytesIO(zip_content), "r") as zip_ref:
            infos = zip_ref.infolist()
            has_assets_dir = any(
                PurePosixPath(info.filename).parts[:1] == ("assets",)
                for info in infos
            )
            planned: list[tuple[zipfile.ZipInfo, Path]] = []
            planned_targets: set[Path] = set()
            total_size = 0

            for info in infos:
                if info.is_dir():
                    continue
                if info.file_size > MAX_ASSET_FILE_BYTES:
                    raise AssistantAssetsZipError(
                        f"Zip member is too large: {info.filename}"
                    )
                total_size += info.file_size
                if total_size > MAX_ASSETS_TOTAL_BYTES:
                    raise AssistantAssetsZipError("Uncompressed assets are too large")
                item = _normalise_asset_member(
                    info, has_assets_dir=has_assets_dir, assets_dir=temp_assets_dir
                )
                if item:
                    if item[1] in planned_targets:
                        raise AssistantAssetsZipError(
                            f"Duplicate zip target is not allowed: {info.filename}"
                        )
                    planned_targets.add(item[1])
                    planned.append(item)

            if not planned:
                raise AssistantAssetsZipError("Zip does not contain asset files")
            if len(planned) > MAX_ASSET_FILE_COUNT:
                raise AssistantAssetsZipError("Zip contains too many asset files")

            for info, target in planned:
                target.parent.mkdir(parents=True, exist_ok=True)
                with zip_ref.open(info) as source, target.open("wb") as dest:
                    shutil.copyfileobj(source, dest)

        if assets_dir.exists():
            os.replace(assets_dir, backup_dir)
            moved_existing = True
        os.replace(temp_assets_dir, assets_dir)
        if moved_existing:
            _remove_path(backup_dir)
        return assets_dir
    except Exception:
        if moved_existing and not assets_dir.exists() and backup_dir.exists():
            os.replace(backup_dir, assets_dir)
        raise
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root, ignore_errors=True)
        if backup_dir.exists():
            _remove_path(backup_dir)
