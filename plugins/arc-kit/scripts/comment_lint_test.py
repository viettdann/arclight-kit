import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "comment-lint.py")
WRAP_A = "  // Validate the edge list against the group's mission id set: each endpoint must"
WRAP_B = "  // be a member, with no self-loops and no duplicates."
LONG = "  // " + "x" * 150
MID = "  // " + "x" * 100


def run(tool, tool_input, options=None, **payload):
    env = {k: v for k, v in os.environ.items() if not k.startswith("ARC_COMMENT_LINT_")}
    env.update({f"ARC_{k}": v for k, v in (options or {}).items()})
    data = json.dumps({"tool_name": tool, "tool_input": tool_input, **payload})
    return subprocess.run([sys.executable, SCRIPT], input=data, capture_output=True, text=True, env=env)


class CommentLintTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root)

    def save(self, name, content):
        path = os.path.join(self.root, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def patch(self, body, options=None, **payload):
        return run("apply_patch", {"command": f"*** Begin Patch\n{body}\n*** End Patch"}, options, cwd=self.root, **payload)

    def edit(self, name, before, old, new):
        self.save(name, before.replace(old, new, 1))
        body = [f"*** Update File: {name}", "@@"]
        body += ["-" + line for line in old.splitlines()]
        body += ["+" + line for line in new.splitlines()]
        return self.patch("\n".join(body))

    def write(self, name, content, options=None):
        self.save(name, content)
        return self.patch(f"*** Add File: {name}\n" + "\n".join("+" + line for line in content.splitlines()), options)

    def test_wrapped_comment_nudges(self):
        r = self.edit("a.ts", "const a = 1\n", "const a = 1\n", f"{WRAP_A}\n{WRAP_B}\nconst a = 1\n")
        self.assertEqual(r.returncode, 2)
        self.assertIn("a.ts:1-2: wrapped comment \"Validate the edge list against the group's mission...\"", r.stderr)

    def test_independent_short_comments_pass(self):
        new = "# This is comment 1\n# This is another comment\nx = 1\n"
        self.assertEqual(self.edit("a.py", "x = 1\n", "x = 1\n", new).returncode, 0)

    def test_long_comment_nudges(self):
        r = self.edit("a.ts", "const a = 1\n", "const a = 1\n", f"{LONG}\nconst a = 1\n")
        self.assertEqual(r.returncode, 2)
        self.assertIn("a.ts:1: comment 155 cols > 150 \"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...\"", r.stderr)

    def test_width_option_overrides_default(self):
        self.assertEqual(self.write("a.ts", MID + "\n").returncode, 0)
        r = self.write("a.ts", MID + "\n", {"COMMENT_LINT_WIDTH": "100"})
        self.assertEqual(r.returncode, 2)
        self.assertIn("comment 105 cols > 100", r.stderr)

    def test_invalid_width_uses_default(self):
        for width in ("garbage", "NaN", "inf"):
            self.assertEqual(self.write("a.ts", LONG, {"COMMENT_LINT_WIDTH": width}).returncode, 2)

    def test_disabled_option_passes(self):
        self.assertEqual(self.write("a.ts", LONG, {"COMMENT_LINT_ENABLED": "false"}).returncode, 0)

    def test_long_comment_with_url_passes(self):
        new = "  // see https://example.com/" + "a" * 100 + "\nconst a = 1\n"
        self.assertEqual(self.edit("a.ts", "const a = 1\n", "const a = 1\n", new).returncode, 0)

    def test_directive_passes(self):
        new = "  // biome-ignore lint/suspicious/noExplicitAny: " + "r" * 80 + "\nconst a = 1\n"
        self.assertEqual(self.edit("a.ts", "const a = 1\n", "const a = 1\n", new).returncode, 0)

    def test_unicode_banner_nudges(self):
        new = "// ───── GET / ─────\nconst a = 1\n"
        r = self.edit("a.ts", "const a = 1\n", "const a = 1\n", new)
        self.assertEqual(r.returncode, 2)
        self.assertIn("banner", r.stderr)

    def test_multiline_block_nudges(self):
        new = "/**\n * Renders the list.\n */\nconst a = 1\n"
        r = self.edit("a.ts", "const a = 1\n", "const a = 1\n", new)
        self.assertEqual(r.returncode, 2)
        self.assertIn("a.ts:1-3: multi-line block comment \"Renders the list.\"", r.stderr)

    def test_single_line_block_passes(self):
        new = "/** Never empty. */\nconst a = 1\n"
        self.assertEqual(self.edit("a.ts", "const a = 1\n", "const a = 1\n", new).returncode, 0)

    def test_glob_string_passes(self):
        new = 'const g = "src/**/*.ts"\nconst h = "*/"\n'
        self.assertEqual(self.edit("a.ts", "const a = 1\n", "const a = 1\n", new).returncode, 0)

    def test_untouched_existing_violation_passes(self):
        before = f"{LONG}\nconst a = 1\nconst b = 2\n"
        self.assertEqual(self.edit("a.ts", before, "const b = 2\n", "const b = 3\n").returncode, 0)

    def test_line_appended_to_existing_comment_nudges(self):
        before = f"{WRAP_A}\nconst a = 1\n"
        r = self.edit("a.ts", before, f"{WRAP_A}\n", f"{WRAP_A}\n{WRAP_B}\n")
        self.assertEqual(r.returncode, 2)
        self.assertIn("a.ts:1-2: wrapped comment", r.stderr)

    def test_generated_file_skipped(self):
        self.assertEqual(self.write("routeTree.gen.ts", f"{LONG}\n").returncode, 0)

    def test_write_untracked_nudges(self):
        self.assertEqual(self.write("a.ts", f"{LONG}\nconst a = 1\n").returncode, 2)

    def test_multiple_files_and_move_and_delete(self):
        self.save("one.ts", LONG + "\n")
        self.save("new.py", "# ---- banner\nx = 2\n")
        r = self.patch(f"*** Add File: one.ts\n+{LONG}\n*** Delete File: gone.ts\n*** Update File: old.py\n*** Move to: new.py\n@@\n-x = 1\n+# ---- banner\n+x = 2")
        self.assertEqual(r.returncode, 2)
        self.assertIn("one.ts:1:", r.stderr)
        self.assertIn("new.py:1:", r.stderr)
        self.assertNotIn("gone.ts", r.stderr)

    def test_multiple_hunks_with_identical_added_lines(self):
        self.save("a.ts", f"first()\n{LONG}\nmiddle()\nsecond()\n{LONG}\nlast()\n")
        r = self.patch(f"*** Update File: a.ts\n@@\n first()\n+{LONG}\n middle()\n@@\n second()\n+{LONG}\n last()")
        self.assertEqual(r.returncode, 2)
        self.assertIn("a.ts:2:", r.stderr)
        self.assertIn("a.ts:5:", r.stderr)

    def test_context_repeated_comment_not_treated_as_added(self):
        self.save("a.ts", f"{LONG}\n{LONG}\nrun()\n")
        r = self.patch(f"*** Update File: a.ts\n@@\n {LONG}\n+{LONG}\n run()")
        self.assertEqual(r.returncode, 2)
        self.assertIn("a.ts:2:", r.stderr)
        self.assertNotIn("a.ts:1:", r.stderr)

    def test_ambiguous_context_is_skipped(self):
        self.save("a.ts", f"start()\n{LONG}\nend()\nstart()\n{LONG}\nend()\n")
        r = self.patch(f"*** Update File: a.ts\n@@\n start()\n+{LONG}\n end()")
        self.assertEqual(r.returncode, 0)

    def test_anchor_disambiguates_repeated_context(self):
        self.save("a.ts", f"start()\n{LONG}\nend()\nfunction target()\nstart()\n{LONG}\nend()\n")
        r = self.patch(f"*** Update File: a.ts\n@@ function target()\n start()\n+{LONG}\n end()")
        self.assertEqual(r.returncode, 2)
        self.assertIn("a.ts:6:", r.stderr)
        self.assertNotIn("a.ts:2:", r.stderr)

    def test_end_of_file_disambiguates(self):
        self.save("a.ts", f"start()\n{LONG}\nstart()\n{LONG}\n")
        r = self.patch(f"*** Update File: a.ts\n@@\n start()\n+{LONG}\n*** End of File")
        self.assertEqual(r.returncode, 2)
        self.assertIn("a.ts:4:", r.stderr)
        self.assertNotIn("a.ts:2:", r.stderr)

    def test_pure_append_uses_file_end(self):
        self.save("a.ts", f"{LONG}\nrun()\n{LONG}\n")
        r = self.patch(f"*** Update File: a.ts\n@@\n+{LONG}")
        self.assertEqual(r.returncode, 2)
        self.assertIn("a.ts:3:", r.stderr)
        self.assertNotIn("a.ts:1:", r.stderr)

    def test_delete_only_update_passes(self):
        self.save("a.ts", LONG + "\n")
        self.assertEqual(self.patch("*** Update File: a.ts\n@@\n-removed()").returncode, 0)

    def test_blank_context_and_whitespace_fuzzy_context(self):
        self.save("a.ts", f"start()   \n\n{LONG}\nend()\n")
        r = self.patch(f"*** Update File: a.ts\n@@\n start()\n\n+{LONG}\n end()")
        self.assertEqual(r.returncode, 2)
        self.assertIn("a.ts:3:", r.stderr)

    def test_unrelated_uncommitted_comment_is_ignored(self):
        self.save("a.ts", "run()\n")
        for args in (("init", "-q"), ("add", "a.ts"), ("commit", "-qm", "initial")):
            subprocess.run(["git", "-C", self.root, "-c", "user.email=t@t", "-c", "user.name=t", *args], check=True, capture_output=True)
        self.save("a.ts", f"{LONG}\nrunAgain()\n")
        r = self.patch("*** Update File: a.ts\n@@\n-run()\n+runAgain()")
        self.assertEqual(r.returncode, 0)

    def test_symlink_loop_skipped(self):
        os.symlink("loop.ts", os.path.join(self.root, "loop.ts"))
        self.assertEqual(self.patch(f"*** Add File: loop.ts\n+{LONG}").returncode, 0)

    def test_non_utf8_file_skipped(self):
        with open(os.path.join(self.root, "a.ts"), "wb") as f:
            f.write(b"\xff")
        self.assertEqual(self.patch(f"*** Add File: a.ts\n+{LONG}").returncode, 0)

    def test_missing_and_changed_files_skipped(self):
        self.assertEqual(self.patch(f"*** Add File: missing.ts\n+{LONG}").returncode, 0)
        self.save("a.ts", "different()\n")
        self.assertEqual(self.patch(f"*** Add File: a.ts\n+{LONG}").returncode, 0)

    def test_absolute_workspace_path_supported(self):
        path = os.path.join(self.root, "a.ts")
        self.assertEqual(self.write(path, LONG).returncode, 2)

    def test_paths_outside_workspace_skipped(self):
        with tempfile.TemporaryDirectory() as outside:
            path = os.path.join(outside, "a.ts")
            with open(path, "w") as f:
                f.write(LONG)
            os.symlink(outside, os.path.join(self.root, "linked"))
            for name in (path, os.path.relpath(path, self.root), "linked/a.ts"):
                self.assertEqual(self.patch(f"*** Add File: {name}\n+{LONG}").returncode, 0)

    def test_large_file_skipped(self):
        self.save("a.ts", LONG + "\n" + "x" * 2_000_000)
        self.assertEqual(self.patch(f"*** Update File: a.ts\n@@\n+{LONG}").returncode, 0)

    def test_explicit_files_checks_all_lines_without_stdin(self):
        self.save("a.ts", LONG + "\n")
        self.save("b.py", "# ---- banner\n")
        r = subprocess.run([sys.executable, SCRIPT, "--files", "a.ts", "b.py"], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("a.ts:1:", r.stderr)
        self.assertIn("b.py:1:", r.stderr)

    def test_malformed_patch_passes(self):
        for patch in (None, {}, "", "*** Begin Patch\n*** Update File: a.ts\n", "*** Begin Patch\n*** Update File: a.ts\n???\n*** End Patch"):
            r = run("apply_patch", {"command": patch}, cwd=self.root)
            self.assertEqual(r.returncode, 0)
            self.assertNotIn("Traceback", r.stderr)

    def test_non_object_payload_passes(self):
        for data in ("[]", "null", "123", '{"tool_name": "apply_patch", "tool_input": []}'):
            r = subprocess.run([sys.executable, SCRIPT], input=data, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0)

    def test_markdown_narrative_heading_nudges(self):
        r = self.write("plan.md", "# Plan\n\n## Rationale\n\nBecause.\n")
        self.assertEqual(r.returncode, 2)
        self.assertIn("plan.md:3: narrative section heading \"Rationale\"", r.stderr)

    def test_markdown_code_comment_ignored(self):
        self.assertEqual(self.write("a.md", f"```ts\n{LONG}\n```\n").returncode, 0)

    def test_other_tool_ignored(self):
        self.assertEqual(run("Read", {"file_path": "/nonexistent.ts"}).returncode, 0)

    def test_bad_payload_passes(self):
        r = subprocess.run([sys.executable, SCRIPT], input="not json", capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
