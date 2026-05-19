import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from Config import Config
from services.assistant_paths import (
    AssistantAssetsZipError,
    AssistantPathError,
    replace_assets_from_zip,
    resolve_assistant_dir,
    validate_assistant_name,
)


class AssistantPathTests(unittest.TestCase):
    def setUp(self):
        self._old_agents_path = Config.BASE_AGENTS_PATH
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "data" / "agents"
        self.root.mkdir(parents=True)
        Config.BASE_AGENTS_PATH = str(self.root)

    def tearDown(self):
        Config.BASE_AGENTS_PATH = self._old_agents_path
        self.tmp.cleanup()

    def make_assistant(self, name="Chat"):
        assistant_dir = self.root / name
        (assistant_dir / "assets").mkdir(parents=True)
        return assistant_dir

    def make_zip(self, entries):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for name, content in entries.items():
                zip_file.writestr(name, content)
        return buffer.getvalue()

    def test_rejects_path_like_assistant_names(self):
        for name in ("../evil", "a/b", "a\\b", "/tmp/evil", "", " padded "):
            with self.subTest(name=name):
                with self.assertRaises(AssistantPathError):
                    validate_assistant_name(name)

    def test_rejects_symlink_escape_from_agents_root(self):
        outside = Path(self.tmp.name) / "outside"
        outside.mkdir()
        (self.root / "Linked").symlink_to(outside, target_is_directory=True)

        with self.assertRaises(AssistantPathError):
            resolve_assistant_dir("Linked", must_exist=True)

    def test_rejects_zip_slip_without_replacing_existing_assets(self):
        assistant_dir = self.make_assistant()
        existing = assistant_dir / "assets" / "keep.txt"
        existing.write_text("keep", encoding="utf-8")
        payload = self.make_zip({"assets/../data_base/tmp/labels/payload.pkl": b"x"})

        with self.assertRaises(AssistantAssetsZipError):
            replace_assets_from_zip("Chat", payload)

        self.assertEqual(existing.read_text(encoding="utf-8"), "keep")
        self.assertFalse((assistant_dir / "data_base" / "tmp" / "labels" / "payload.pkl").exists())

    def test_replaces_assets_with_safe_zip_members_only(self):
        assistant_dir = self.make_assistant()
        (assistant_dir / "assets" / "old.txt").write_text("old", encoding="utf-8")
        payload = self.make_zip({
            "assets/images/avatar.png": b"png",
            "ignored.txt": b"ignored",
        })

        replace_assets_from_zip("Chat", payload)

        self.assertFalse((assistant_dir / "assets" / "old.txt").exists())
        self.assertEqual((assistant_dir / "assets" / "images" / "avatar.png").read_bytes(), b"png")
        self.assertFalse((assistant_dir / "assets" / "ignored.txt").exists())


if __name__ == "__main__":
    unittest.main()
