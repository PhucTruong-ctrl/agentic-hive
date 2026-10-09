"""Installer regressions in temporary trees; account commands are mocked."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parent.parent


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.env = dict(os.environ, DESTDIR=str(self.root))
        self.command = [str(REPO / "install/hive-install"), "--beekeeper", "alice", "--no-deps"]

    def install(self, *args, success=True):
        result = subprocess.run(self.command + list(args), env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, success, result.stderr)
        return result

    def test_settings_survive_reinstall_uninstall(self):
        config = self.root / "etc/claude-code/managed-settings.json"
        config.parent.mkdir(parents=True)
        original = {"permissions": {"deny": ["Bash(rm *)"]}, "statusLine": {"command": "company-status"},
                    "hooks": {"SessionStart": [{"hooks": [{"command": "company-hook"}]}]}}
        config.write_text(json.dumps(original))
        executable = self.root / "usr/local/bin/hive"
        executable.parent.mkdir(parents=True)
        executable.write_text("original executable\n")
        self.install()
        self.install()
        merged = json.loads(config.read_text())
        self.assertEqual(merged["permissions"], original["permissions"])
        self.assertEqual(merged["statusLine"], original["statusLine"])
        self.assertEqual(len(merged["hooks"]["SessionStart"]), 2)
        self.install("--uninstall")
        self.assertEqual(json.loads(config.read_text()), original)
        self.assertEqual(executable.read_text(), "original executable\n")

    def test_later_policy_changes_survive_uninstall(self):
        self.install()
        config = self.root / "etc/claude-code/managed-settings.json"
        current = json.loads(config.read_text())
        current["permissions"] = {"deny": ["Bash(rm *)"]}
        current["hooks"]["SessionStart"].append({"hooks": [{"command": "company-hook"}]})
        config.write_text(json.dumps(current))
        self.install("--uninstall")
        remaining = json.loads(config.read_text())
        self.assertEqual(remaining["permissions"], current["permissions"])
        self.assertEqual(remaining["hooks"], {"SessionStart": [{"hooks": [{"command": "company-hook"}]}]})
        self.assertNotIn("statusLine", remaining)

    def test_symlinked_settings_target_is_restored(self):
        target = self.root / "company/settings.json"
        target.parent.mkdir()
        original = '{"permissions":{"deny":["Bash(*)"]}}'
        target.write_text(original)
        config = self.root / "etc/claude-code/managed-settings.json"
        config.parent.mkdir(parents=True)
        config.symlink_to(target)
        self.install()
        self.assertTrue(config.is_symlink())
        self.assertIn("hooks", json.loads(target.read_text()))
        self.install("--uninstall")
        self.assertTrue(config.is_symlink())
        self.assertEqual(target.read_text(), original)

    def test_no_hooks_does_not_claim_existing_policy(self):
        config = self.root / "etc/claude-code/managed-settings.json"
        config.parent.mkdir(parents=True)
        config.write_text('{"permissions":{"deny":["Bash(*)"]}}')
        self.install("--no-hooks")
        self.install("--uninstall")
        self.assertEqual(config.read_text(), '{"permissions":{"deny":["Bash(*)"]}}')

    def test_invalid_policy_is_not_overwritten(self):
        config = self.root / "etc/claude-code/managed-settings.json"
        config.parent.mkdir(parents=True)
        config.write_text("broken JSON")
        self.install(success=False)
        self.assertEqual(config.read_text(), "broken JSON")

    def test_custom_configuration_reaches_runtime(self):
        args = ("--hive-user", "worker", "--hive-root", "/opt/habitat")
        self.install(*args)
        profile = (self.root / "etc/profile.d/agentic-hive.sh").read_text()
        unit = (self.root / "etc/systemd/system/hive-web.service").read_text()
        self.assertIn("export HIVE_USER=worker", profile)
        self.assertIn("export HIVE_ROOT=/opt/habitat", profile)
        self.assertIn("Environment=HIVE_USER=worker", unit)
        self.assertIn("Environment=HIVE_BIN_DIR=/usr/local/bin", unit)
        self.install("--uninstall", success=False)
        self.assertTrue((self.root / "usr/local/bin/hive").exists())
        self.install(*args, "--uninstall")

    def test_untracked_installation_is_not_deleted(self):
        result = self.install("--uninstall", success=False)
        self.assertIn("ownership journal", result.stderr)

    def functions(self, commands):
        source = (REPO / "install/hive-install").read_text().split("# --- main ")[0]
        script = f"set -- --beekeeper alice --dry-run\n{source}\n"
        script += f"STATE_HELPER={shlex.quote(str(REPO / 'install/hive-state.py'))}\n"
        script += f"STATE_DIR={shlex.quote(str(self.root / 'journal'))}\nDRY_RUN=0\nSTAGE=\n"
        script += f"HIVE_HOME={shlex.quote(str(self.root))}\nstate init \"$(state_options)\"\n"
        script_path = self.root / "functions.sh"
        script_path.write_text(script + commands)
        result = subprocess.run(["bash", "--noprofile", "--norc", str(script_path)],
                                capture_output=True, text=True, cwd=REPO)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_reused_accounts_and_membership_are_never_removed(self):
        output = self.functions('''
getent() { if [[ $1 == passwd ]]; then printf 'hive:x:1001:1001::%s:/bin/bash\\n' "$HIVE_HOME"; fi; }
id() { [[ $1 != -nG ]] || echo hive; }
systemctl() { :; }
userdel() { echo BAD-userdel; }
groupdel() { echo BAD-groupdel; }
gpasswd() { echo BAD-gpasswd; }
create_account
uninstall
''')
        self.assertNotIn("BAD-", output)

    def test_owned_account_removed_without_removing_home(self):
        output = self.functions('''
getent() { return 1; }
id() { if [[ $1 == -nG ]]; then echo users; else return 1; fi; }
groupadd() { :; }
useradd() { :; }
usermod() { :; }
systemctl() { :; }
userdel() { echo "USERDEL=$*"; }
groupdel() { echo "GROUPDEL=$*"; }
gpasswd() { echo "GPASSWD=$*"; }
create_account
[[ $(state get created_user) == true ]]
uninstall
''')
        self.assertIn("USERDEL=hive", output)
        self.assertNotIn("--remove", output)
        self.assertTrue(self.root.exists())

    def test_package_names(self):
        for row in (REPO / "install/hive-install").read_text().splitlines():
            if "install -y|" in row or "pacman -S " in row or "install|" in row:
                self.assertIn("findutils", row)
                self.assertNotIn(" sed find sudo ", row)


if __name__ == "__main__":
    unittest.main()
