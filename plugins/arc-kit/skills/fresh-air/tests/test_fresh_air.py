"""Regression tests; every config write is confined to a temporary directory."""

import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "fresh_air.py"
spec = importlib.util.spec_from_file_location("fresh_air", SCRIPT)
fresh_air = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fresh_air)


class FreshAirTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.root = self.base / "project"
        self.root.mkdir()
        self.config = self.base / "codex" / "config.toml"
        self.config.parent.mkdir()

    def skill(self, name="example", root=None):
        path = (root or self.root) / ".agents" / "skills" / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("---\nname: example\ndescription: Test fixture\n---\n", encoding="utf-8")
        return path

    def run_operation(self, command="off", root=None, dry_run=False):
        return fresh_air.operate(command, root or self.root, self.config, (), dry_run)

    def test_round_trip_preserves_bytes_and_permissions(self):
        self.skill()
        original = b'# user comment\r\nmodel = "example"\r\n[features]\r\nshell_tool = true'
        self.config.write_bytes(original)
        self.config.chmod(0o640)
        self.assertTrue(self.run_operation()["changed"])
        self.assertTrue(self.config.read_bytes().startswith(original))
        self.assertEqual(stat.S_IMODE(self.config.stat().st_mode), 0o640)
        self.assertTrue(self.run_operation("restore")["changed"])
        self.assertEqual(self.config.read_bytes(), original)
        self.assertFalse(self.run_operation("restore")["changed"])

    def test_repeated_off_is_idempotent_and_includes_new_skills(self):
        first = self.skill()
        self.run_operation()
        initial = self.config.read_bytes()
        self.assertFalse(self.run_operation()["changed"])
        self.assertEqual(self.config.read_bytes(), initial)
        second = self.skill("new")
        first.unlink()
        result = self.run_operation()
        self.assertEqual(set(result["managed"]), {str(first), str(second)})
        self.assertTrue(result["changed"])

    def test_existing_enabled_and_disabled_entries_are_not_owned(self):
        enabled = self.skill("enabled")
        disabled = self.skill("disabled")
        added = self.skill("new")
        original = (
            f'[[skills.config]]\npath = {json.dumps(str(enabled))}\nenabled = true\n'
            f'[[skills.config]]\npath = {json.dumps(str(disabled))}\nenabled = false\n'
        ).encode()
        self.config.write_bytes(original)
        result = self.run_operation()
        self.assertEqual(result["managed"], [str(added)])
        self.assertEqual(len(result["preserved_user_entries"]), 2)
        parsed = fresh_air.configured_skills(self.config.read_bytes())
        self.assertTrue(parsed[enabled])
        self.assertFalse(parsed[disabled])
        self.run_operation("restore")
        self.assertEqual(self.config.read_bytes(), original)

    def test_restoring_one_project_preserves_other_project(self):
        second_root = self.base / "other-project"
        second_root.mkdir()
        first, second = self.skill(), self.skill(root=second_root)
        self.run_operation()
        self.run_operation(root=second_root)
        self.run_operation("restore")
        self.assertEqual(fresh_air.configured_skills(self.config.read_bytes()), {second: False})
        self.assertNotIn(str(first).encode(), self.config.read_bytes())
        self.run_operation("restore", root=second_root)
        self.assertEqual(self.config.read_bytes(), b"")

    def test_unrelated_user_tables_appended_after_block_are_preserved(self):
        self.skill()
        self.run_operation()
        addition = b'\n[features]\nshell_tool = true\n'
        self.config.write_bytes(self.config.read_bytes() + addition)
        current = self.config.read_bytes()
        self.assertFalse(self.run_operation()["changed"])
        self.assertEqual(self.config.read_bytes(), current)
        self.skill("new")
        self.run_operation()
        self.run_operation("restore")
        self.assertEqual(self.config.read_bytes(), addition)

    def test_edited_owned_block_is_not_overwritten(self):
        self.skill()
        self.run_operation()
        modified = self.config.read_bytes().replace(b"enabled = false", b"enabled = true")
        self.config.write_bytes(modified)
        for command in ("off", "restore"):
            with self.assertRaisesRegex(fresh_air.Conflict, "edited"):
                self.run_operation(command)
        self.assertEqual(self.config.read_bytes(), modified)

    def test_user_fields_added_to_managed_table_outside_marker_are_not_removed(self):
        self.skill()
        self.run_operation()
        modified = self.config.read_bytes() + b"custom = true\n"
        self.config.write_bytes(modified)
        with self.assertRaisesRegex(fresh_air.Conflict, "extra user fields"):
            self.run_operation("restore")
        self.assertEqual(self.config.read_bytes(), modified)

    def test_invalid_toml_and_relative_paths_fail_without_writes(self):
        self.skill()
        for raw in (b"[broken", b'[[skills.config]]\npath = "relative/SKILL.md"\nenabled = false\n'):
            self.config.write_bytes(raw)
            with self.assertRaises(fresh_air.Conflict):
                self.run_operation()
            self.assertEqual(self.config.read_bytes(), raw)

    def test_duplicate_user_entry_for_managed_path_fails_without_writes(self):
        path = self.skill()
        self.run_operation()
        modified = self.config.read_bytes() + f'[[skills.config]]\npath = {json.dumps(str(path))}\nenabled = true\n'.encode()
        self.config.write_bytes(modified)
        with self.assertRaisesRegex(fresh_air.Conflict, "Duplicate"):
            self.run_operation("restore")
        self.assertEqual(self.config.read_bytes(), modified)

    def test_status_and_dry_run_do_not_write(self):
        path = self.skill()
        self.assertEqual(self.run_operation("status")["discovered"], [str(path)])
        self.assertTrue(self.run_operation(dry_run=True)["changed"])
        self.assertFalse(self.config.exists())

    def test_markers_inside_multiline_strings_never_modify_config(self):
        path = self.skill()
        for quote in (b'"""', b"'''"):
            for command in ("status", "off", "restore"):
                with self.subTest(quote=quote, command=command):
                    raw = b"note = " + quote + b"\n" + fresh_air.make_block(self.root, {path}) + quote + b"\n"
                    self.config.write_bytes(raw)
                    self.assertEqual(fresh_air.configured_skills(raw), {})
                    with self.assertRaisesRegex(fresh_air.Conflict, "not active disabled skill entries"):
                        self.run_operation(command)
                    self.assertEqual(self.config.read_bytes(), raw)

    def test_nested_skills_and_internal_symlinks_are_discovered(self):
        first = self.skill()
        nested = self.skill("nested", root=self.root / "packages" / "nested")
        shared = self.root / "shared" / "SKILL.md"
        shared.parent.mkdir()
        shared.write_text("data only", encoding="utf-8")
        skills = self.root / ".agents" / "skills"
        (skills / "alias").symlink_to(shared.parent, target_is_directory=True)
        (skills / "duplicate").symlink_to(first.parent, target_is_directory=True)
        (shared.parent / "cycle").symlink_to(shared.parent, target_is_directory=True)
        found, _ = fresh_air.discover(self.root, ())
        self.assertEqual(set(found), {first, nested, shared})

    def test_external_and_protected_skill_links_are_skipped(self):
        owned = self.skill()
        external = self.skill("personal", root=self.base / "outside")
        skills = self.root / ".agents" / "skills"
        (skills / "external").symlink_to(external.parent, target_is_directory=True)
        protected = self.root / "user-scoped-skills"
        protected_skill = self.skill(root=protected)
        (skills / "protected").symlink_to(protected_skill.parent, target_is_directory=True)
        found, skipped = fresh_air.discover(self.root, (protected,))
        self.assertEqual(found, [owned])
        self.assertTrue(any("outside project" in item for item in skipped))
        self.assertTrue(any("personal or system" in item for item in skipped))

    def test_home_and_personal_roots_are_rejected(self):
        with patch.object(Path, "home", return_value=self.root):
            for target in (self.root, self.base):
                with self.assertRaises(fresh_air.Conflict):
                    fresh_air.validate_root(target, ())
        with self.assertRaises(fresh_air.Conflict):
            fresh_air.validate_root(self.root / "child", (self.root,))

    def test_lock_prevents_concurrent_writes_and_is_released(self):
        with fresh_air.config_lock(self.config):
            with self.assertRaisesRegex(fresh_air.Conflict, "locked"):
                with fresh_air.config_lock(self.config):
                    self.fail("second writer acquired lock")
        self.assertFalse((self.config.parent / ".fresh-air.lock").exists())

    def test_concurrent_config_change_is_not_overwritten(self):
        self.config.write_bytes(b'# concurrent edit\n')
        with self.assertRaisesRegex(fresh_air.Conflict, "changed during"):
            fresh_air.atomic_write(self.config, b'# original\n', b'# replacement\n', True)
        self.assertEqual(self.config.read_bytes(), b'# concurrent edit\n')
        self.assertEqual(list(self.config.parent.glob(".fresh-air-*")), [])

    def test_unicode_and_quoted_paths_form_valid_toml(self):
        path = self.skill('tiếng Việt 🚀 "quote"')
        self.run_operation()
        self.assertEqual(fresh_air.configured_skills(self.config.read_bytes()), {path: False})
        self.run_operation("restore")
        self.assertEqual(self.config.read_bytes(), b"")

    def test_cli_uses_only_isolated_codex_home_and_git_root(self):
        self.skill()
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        nested = self.root / "src"
        nested.mkdir()
        env = dict(os.environ, CODEX_HOME=str(self.config.parent))
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "off", str(nested), "--json"],
            env=env, capture_output=True, text=True, check=True,
        )
        report = json.loads(result.stdout)
        self.assertEqual(report["project"], str(self.root))
        self.assertEqual(report["config"], str(self.config))
        self.assertTrue(report["changed"])
        subprocess.run(
            [sys.executable, str(SCRIPT), "restore", str(self.root)],
            env=env, capture_output=True, text=True, check=True,
        )
        self.assertEqual(self.config.read_bytes(), b"")


if __name__ == "__main__":
    unittest.main()
