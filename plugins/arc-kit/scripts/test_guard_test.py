import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test-guard.py")


def run(tool, tool_input, options=None, **payload):
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE_PLUGIN_OPTION_")}
    env.update(options or {})
    data = json.dumps({"tool_name": tool, "tool_input": tool_input, **payload})
    return subprocess.run([sys.executable, SCRIPT], input=data, capture_output=True, text=True, env=env)


class TestGuardTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.session = str(uuid.uuid4())

    def tearDown(self):
        shutil.rmtree(self.root)

    def write(self, name, content, session=None, options=None, **payload):
        path = os.path.join(self.root, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return run("Write", {"file_path": path, "content": content}, options, session_id=session or self.session, **payload)

    def edit(self, name, before, old, new):
        path = os.path.join(self.root, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(before.replace(old, new, 1))
        return run("Edit", {"file_path": path, "old_string": old, "new_string": new}, session_id=self.session)

    def git(self, *args):
        subprocess.run(
            ["git", "-C", self.root, "-c", "user.email=t@t", "-c", "user.name=t", *args],
            check=True, capture_output=True,
        )

    def test_new_cases_are_named_per_language(self):
        cases = {
            "a_test.py": ("def test_parses_empty():\n    assert parse('') == []\n", "test_parses_empty"),
            "a.test.ts": ("test.each([[1, 2]])('adds %i', (a, b) => {})\n", "adds %i"),
            "a.spec.js": ("it('rejects expired token', () => {})\n", "rejects expired token"),
            "a_test.go": ("func TestRetry(t *testing.T) {}\n", "TestRetry"),
            "ParserTests.cs": ("[Theory]\n[InlineData(\"call foo()\")]\npublic async Task Parses_Number(string s) {}\n", "Parses_Number"),
            "ParserTest.java": ("@Test\n@DisplayName(\"when calling foo()\")\nvoid parsesNumber() {}\n", "parsesNumber"),
            "ParserTest.kt": ("@Test fun `parses number`() {}\n", "parses number"),
            "parser_test.rs": ("#[tokio::test]\nasync fn parses_number() {}\n", "parses_number"),
            "ParserTest.php": ("#[Test]\npublic function parsesNumber(): void {}\n", "parsesNumber"),
            "ParserTests.swift": ("func testParsesNumber() {}\n", "testParsesNumber"),
            "parser_spec.rb": ("it \"parses a number\" do\nend\n", "parses a number"),
        }
        for name, (content, expected) in cases.items():
            with self.subTest(name=name):
                r = self.write(name, content)
                self.assertEqual(r.returncode, 2, r.stderr)
                self.assertIn(f"{name}:1: {expected}", r.stderr)

    def test_editing_existing_cases_passes(self):
        edits = [
            ("a_test.py", "def test_a():\n    assert f() == 1\n", "assert f() == 1", "assert f() == 2"),
            ("a_test.py", "def test_a():\n    pass\n", "def test_a():", "def test_a(tmp_path):"),
            ("a.test.js", "it('x', () => {})\n", "it('x', () => {})", "describe('g', () => {\n  it('x', async () => {})\n})"),
            ("ATests.cs", "[Fact]\npublic void Foo() {}\n", "[Fact]", "[Fact(Skip = \"flaky\")]"),
        ]
        for name, before, old, new in edits:
            with self.subTest(new=new):
                self.assertEqual(self.edit(name, before, old, new).returncode, 0)

    def test_added_case_in_existing_file_nudges(self):
        r = self.edit("a_test.py", "def test_a():\n    pass\n", "    pass\n", "    pass\n\n\ndef test_b():\n    pass\n")
        self.assertEqual(r.returncode, 2)
        self.assertIn("a_test.py:5: test_b", r.stderr)
        self.assertNotIn("test_a", r.stderr)

    def test_repeated_name_in_another_block_nudges(self):
        before = "describe('a', () => {\n  it('works', () => {})\n})\n"
        new = "describe('a', () => {\n  it('works', () => {})\n})\ndescribe('b', () => {\n  it('works', () => {})\n})\n"
        r = self.edit("a.test.js", before, before, new)
        self.assertEqual(r.returncode, 2)
        self.assertIn("a.test.js:5: works", r.stderr)
        self.assertNotIn("a.test.js:2:", r.stderr)

    def test_write_lists_only_cases_missing_before_it(self):
        self.write("a_test.py", "def test_a():\n    pass\n")
        self.git("init", "-q")
        self.git("add", "a_test.py")
        self.git("commit", "-qm", "init")
        r = self.write("a_test.py", "def test_a():\n    pass\n\n\ndef test_b():\n    pass\n", session=str(uuid.uuid4()))
        self.assertEqual(r.returncode, 2)
        self.assertIn("test_b", r.stderr)
        self.assertNotIn("test_a", r.stderr)
        wip = "def test_a():\n    pass\n\n\ndef test_wip():\n    pass\n"
        r = self.write("a_test.py", wip + "\n\ndef test_c():\n    pass\n", session=str(uuid.uuid4()), tool_response={"originalFile": wip})
        self.assertIn("test_c", r.stderr)
        self.assertNotIn("test_wip", r.stderr)

    def test_non_cases_pass(self):
        files = {
            "latest.py": "def test_x():\n    pass\n",
            "conftest.py": "def test_data():\n    pass\n",
            "latest.md": "```js\nit('x', () => {})\n```\n",
            "b_test.go": "func TestMain(m *testing.M) {}\nfunc testServer(t *testing.T) {}\n",
            "e.spec.ts": "test.describe('login flow', () => {})\n",
        }
        for name, content in files.items():
            with self.subTest(name=name):
                self.assertEqual(self.write(name, content).returncode, 0)

    def test_case_questioned_once_per_session(self):
        content = "def test_a():\n    pass\n"
        self.assertEqual(self.write("a_test.py", content).returncode, 2)
        self.assertEqual(self.write("a_test.py", content).returncode, 0)
        self.assertEqual(self.write("a_test.py", content, session=str(uuid.uuid4())).returncode, 2)

    def test_disabled_option_passes(self):
        r = self.write("a_test.py", "def test_a():\n    pass\n", options={"CLAUDE_PLUGIN_OPTION_TEST_GUARD_ENABLED": "false"})
        self.assertEqual(r.returncode, 0)

    def test_bad_payload_passes(self):
        r = subprocess.run([sys.executable, SCRIPT], input="not json", capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
