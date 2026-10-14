import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dotnet-guard.py")


def run(tool, tool_input, options=None, **payload):
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE_PLUGIN_OPTION_")}
    env.update(options or {})
    data = json.dumps({"tool_name": tool, "tool_input": tool_input, **payload})
    return subprocess.run([sys.executable, SCRIPT], input=data, capture_output=True, text=True, env=env)


class DotnetGuardTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.session = str(uuid.uuid4())

    def tearDown(self):
        shutil.rmtree(self.root)

    def write(self, name, content, options=None, **payload):
        path = os.path.join(self.root, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return run("Write", {"file_path": path, "content": content}, options, session_id=self.session, **payload)

    def edit(self, name, before, old, new):
        path = os.path.join(self.root, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(before.replace(old, new, 1))
        return run("Edit", {"file_path": path, "old_string": old, "new_string": new}, session_id=self.session)

    def test_added_escape_hatches_are_flagged(self):
        cases = [
            ("OrderTests.cs", "[Fact(Skip = \"flaky\")]\npublic void Saves() {}\n", "skipped test"),
            ("OrderTests.cs", "[TestMethod, Ignore]\npublic void Saves() {}\n", "skipped test"),
            ("OrderTests.cs", "Assert.Inconclusive(\"later\");\n", "skipped test"),
            ("Order.cs", "#pragma warning disable CS8618\n", "warning suppressed"),
            ("Order.cs", "[SuppressMessage(\"Style\", \"IDE0060\")]\n", "warning suppressed"),
            ("Order.cs", "#nullable disable\n", "warning suppressed"),
            ("Order.cs", "try { Save(); } catch (Exception) { }\n", "empty catch"),
            ("Order.cs", "try\n{\n    Save();\n}\ncatch\n{\n    // ignore\n}\n", "empty catch"),
            ("Api.Tests/OrderFlow.cs", "await Task.Delay(500);\n", "sleep in a test"),
            ("Api.csproj", "<PropertyGroup><NoWarn>$(NoWarn);CS1591</NoWarn></PropertyGroup>\n", "warning suppressed"),
            ("Api.csproj", "<PackageReference Include=\"X\" NoWarn=\"NU1605\" />\n", "warning suppressed"),
            ("Directory.Build.props", "<TreatWarningsAsErrors>false</TreatWarningsAsErrors>\n", "warning suppressed"),
            ("Api.csproj", "<PackageReference Include=\"Polly\" VersionOverride=\"7.2.4\" />\n", "central package version bypassed"),
            (".editorconfig", "dotnet_diagnostic.CA2007.severity = none\n", "analyzer severity lowered"),
        ]
        for name, content, what in cases:
            with self.subTest(content=content):
                r = self.write(name, content)
                self.assertEqual(r.returncode, 2, r.stderr)
                self.assertIn(what, r.stderr)

    def test_legitimate_code_passes(self):
        cases = [
            ("Order.cs", "catch (Exception ex) { logger.LogError(ex, \"save\"); throw; }\n"),
            ("Order.cs", "await Task.Delay(TimeSpan.FromSeconds(retry), ct);\n"),
            ("Order.cs", "#pragma warning restore CS8618\n"),
            ("Api.csproj", "<TreatWarningsAsErrors>true</TreatWarningsAsErrors>\n"),
            (".editorconfig", "dotnet_diagnostic.CA2007.severity = error\n"),
            ("README.md", "#pragma warning disable CS8618\n"),
            ("obj/Debug/Api.AssemblyInfo.cs", "#pragma warning disable\n"),
        ]
        for name, content in cases:
            with self.subTest(name=name, content=content):
                self.assertEqual(self.write(name, content).returncode, 0)

    def test_existing_suppression_moved_by_an_edit_passes(self):
        before = "#pragma warning disable CS0618\nvar a = 1;\n"
        r = self.edit("Order.cs", before, "var a = 1;", "var a = 2;")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_suppression_added_beside_an_existing_one_is_flagged_once(self):
        before = "#pragma warning disable CS0618\nvar a = 1;\n"
        new = "var a = 1;\n#pragma warning disable CS0618"
        r = self.edit("Order.cs", before, "var a = 1;", new)
        self.assertEqual(r.returncode, 2)
        self.assertIn("Order.cs:3:", r.stderr)
        self.assertEqual(self.edit("Order.cs", before, "var a = 1;", new).returncode, 0)

    def test_write_compares_with_the_replaced_file(self):
        content = "#pragma warning disable CS0618\nvar a = 2;\n"
        r = self.write("Order.cs", content, tool_response={"originalFile": "#pragma warning disable CS0618\nvar a = 1;\n"})
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_option_off_disables(self):
        r = self.write("Order.cs", "#pragma warning disable CS8618\n", {"CLAUDE_PLUGIN_OPTION_DOTNET_GUARD_ENABLED": "false"})
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
