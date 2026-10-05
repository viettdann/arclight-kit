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
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE_PLUGIN_OPTION_")}
    env.update(options or {})
    data = json.dumps({"tool_name": tool, "tool_input": tool_input, **payload})
    return subprocess.run([sys.executable, SCRIPT], input=data, capture_output=True, text=True, env=env)


class CommentLintTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root)

    def edit(self, name, before, old, new, **extra):
        path = os.path.join(self.root, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(before.replace(old, new, 1))
        return run("Edit", {"file_path": path, "old_string": old, "new_string": new, **extra})

    def write(self, name, content):
        path = os.path.join(self.root, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return run("Write", {"file_path": path, "content": content})

    def git(self, *args):
        subprocess.run(
            ["git", "-C", self.root, "-c", "user.email=t@t", "-c", "user.name=t", *args],
            check=True, capture_output=True,
        )

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
        path = os.path.join(self.root, "a.ts")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"{MID}\n")
        self.assertEqual(run("Write", {"file_path": path}).returncode, 0)
        r = run("Write", {"file_path": path}, {"CLAUDE_PLUGIN_OPTION_COMMENT_LINT_WIDTH": "100"})
        self.assertEqual(r.returncode, 2)
        self.assertIn("comment 105 cols > 100", r.stderr)

    def test_disabled_option_passes(self):
        path = os.path.join(self.root, "a.ts")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"{LONG}\n")
        self.assertEqual(run("Write", {"file_path": path}, {"CLAUDE_PLUGIN_OPTION_COMMENT_LINT_ENABLED": "false"}).returncode, 0)

    def test_lowercase_option_name_is_ignored(self):
        path = os.path.join(self.root, "a.ts")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"{LONG}\n")
        self.assertEqual(run("Write", {"file_path": path}, {"CLAUDE_PLUGIN_OPTION_comment_lint_enabled": "false"}).returncode, 2)

    def test_same_tool_use_id_reports_once(self):
        path = os.path.join(self.root, "a.ts")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"{LONG}\n")
        tool_use_id = f"toolu_test_{os.getpid()}_{self.id()}"
        self.assertEqual(run("Write", {"file_path": path}, tool_use_id=tool_use_id).returncode, 2)
        self.assertEqual(run("Write", {"file_path": path}, tool_use_id=tool_use_id).returncode, 0)
        self.assertEqual(run("Write", {"file_path": path}, tool_use_id=tool_use_id + "b").returncode, 2)

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

    def test_write_tracked_only_checks_new_lines(self):
        self.git("init", "-q")
        self.write("a.ts", f"{LONG}\nconst a = 1\n")
        self.git("add", "a.ts")
        self.git("commit", "-q", "-m", "init")
        self.assertEqual(self.write("a.ts", f"{LONG}\nconst a = 2\n").returncode, 0)
        r = self.write("a.ts", f"{LONG}\nconst a = 2\n{LONG}x\n")
        self.assertEqual(r.returncode, 2)
        self.assertIn("a.ts:3:", r.stderr)

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
