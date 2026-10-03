import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from validate_plugins import ROOT, validate


class PackageValidationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "plugins", self.root / "plugins")
        shutil.copytree(ROOT / ".agents", self.root / ".agents")

    def change_json(self, path, edit):
        target = self.root / path
        data = json.loads(target.read_text())
        edit(data)
        target.write_text(json.dumps(data))

    def assert_error(self, message):
        errors, _ = validate(self.root)
        self.assertTrue(any(message in error for error in errors), errors)

    def test_repository_packages(self):
        errors, count = validate(self.root)
        self.assertEqual(errors, [])
        self.assertEqual(count, 20)

    def test_escaping_marketplace_path(self):
        self.change_json(".agents/plugins/marketplace.json", lambda d: d["plugins"][0]["source"].update(path="./../outside"))
        self.assert_error("escaping path")

    def test_duplicate_plugin(self):
        self.change_json(".agents/plugins/marketplace.json", lambda d: d["plugins"].append(copy.deepcopy(d["plugins"][0])))
        self.assert_error("duplicate plugin")

    def test_stale_compatibility_manifest(self):
        self.change_json("plugins/arc-kit/.codex-plugin/plugin.json", lambda d: d.update(version="99.0.0"))
        self.assert_error("fallback differs")

    def test_missing_skill_metadata(self):
        (self.root / "plugins/arc-design/skills/design/agents/openai.yaml").unlink()
        self.assert_error("openai.yaml")

    def test_broken_reference(self):
        with (self.root / "plugins/arc-design/skills/design/SKILL.md").open("a") as f:
            f.write("\nRead `../missing/SKILL.md`.\n")
        self.assert_error("invalid bundled reference")

    def test_legacy_tool_instruction(self):
        with (self.root / "plugins/arc-design/skills/design/SKILL.md").open("a") as f:
            f.write("\nCall AskUserQuestion.\n")
        self.assert_error("legacy runtime instruction")

    def test_missing_reference_without_dot_prefix(self):
        (self.root / "plugins/arc-design/skills/design/references/profile-tool.md").unlink()
        self.assert_error("invalid bundled reference references/profile-tool.md")

    def test_missing_script_in_command(self):
        (self.root / "plugins/arc-design/skills/design/scripts/screenshot.mjs").unlink()
        self.assert_error("invalid bundled reference ./scripts/screenshot.mjs")

    def test_empty_hook_handlers(self):
        self.change_json("plugins/arc-kit/hooks/hooks.json", lambda d: d["hooks"]["PostToolUse"][0].update(hooks=[]))
        self.assert_error("requires one command handler")

    def test_arc_reload_matcher(self):
        self.change_json("plugins/arc-kit/hooks/hooks.json", lambda d: d["hooks"]["SessionStart"][0].update(matcher="startup"))
        self.assert_error("arc reload")

    def test_missing_arc_reload_script(self):
        (self.root / "plugins/arc-kit/scripts/arc-compact.py").unlink()
        self.assert_error("missing or escaping path")

    def test_handoff_explicit_invocation(self):
        path = self.root / "plugins/arc-kit/skills/handoff/agents/openai.yaml"
        path.write_text(path.read_text().replace("allow_implicit_invocation: false", "allow_implicit_invocation: true"))
        self.assert_error("handoff must require explicit invocation")

    def test_explicit_invocation_policy(self):
        path = self.root / "plugins/arc-kit/skills/arc/agents/openai.yaml"
        path.write_text(path.read_text().replace("allow_implicit_invocation: false", "allow_implicit_invocation: true"))
        self.assert_error("explicit invocation")


if __name__ == "__main__":
    unittest.main()
