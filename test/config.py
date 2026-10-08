"""Settings integration preserves user data and only manages Hive commands."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "share"))
from hive_config import merge, update


class ConfigTests(unittest.TestCase):
    def test_mixed_matcher_group_and_idempotence(self):
        old = {"model": "existing", "mcpServers": {"existing": {}}, "hooks": {"SessionStart": [
            {"matcher": "*", "hooks": [{"command": "company-hook"},
                                       {"command": "/old/bin/hive-hook qwen SessionStart"}]}]}}
        desired = {"hooks": {"SessionStart": [{"matcher": "*", "hooks": [
            {"command": "/new/bin/hive-hook qwen SessionStart"}]}]}}
        result = merge(old, desired)
        self.assertEqual(result["model"], old["model"])
        self.assertEqual(result["mcpServers"], old["mcpServers"])
        self.assertEqual(result["hooks"]["SessionStart"][0]["hooks"], [{"command": "company-hook"}])
        self.assertEqual(merge(result, desired), result)
        self.assertEqual(merge(result, desired, remove=True)["hooks"]["SessionStart"][0]["hooks"],
                         [{"command": "company-hook"}])

    def test_flat_cursor_and_top_level_openhands(self):
        for desired in ({"version": 1, "hooks": {"sessionStart": [
                {"command": "hive-hook cursor SessionStart"}]}},
                {"session_start": [{"hooks": [{"command": "hive-hook openhands SessionStart"}]}]}):
            old = {"unrelated": True}
            self.assertTrue(merge(old, desired)["unrelated"])
            self.assertTrue(merge(merge(old, desired), desired, remove=True)["unrelated"])

    def test_file_mode_and_unchanged_mtime(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "settings.json"
            path.write_text('{"model":"existing"}')
            path.chmod(0o600)
            desired = {"hooks": {"SessionStart": [{"hooks": [{"command": "hive-hook qwen SessionStart"}]}]}}
            update(path, desired)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            before = path.stat().st_mtime_ns
            update(path, desired)
            self.assertEqual(path.stat().st_mtime_ns, before)
            self.assertEqual(json.loads(path.read_text())["model"], "existing")

    def test_bad_settings_are_left_intact(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "settings.json"
            for content in ("bad JSON", '{"hooks":{"SessionStart":"bad schema"}}'):
                path.write_text(content)
                with self.assertRaises(ValueError):
                    update(path, {"hooks": {"SessionStart": []}})
                self.assertEqual(path.read_text(), content)


if __name__ == "__main__":
    unittest.main()
