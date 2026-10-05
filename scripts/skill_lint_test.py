import json
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGINS = os.path.join(ROOT, "plugins")
DESCRIPTION_MAX = 930
CATALOG_MAX = 13000
SKILL_BYTES_MAX = 24000
PATH_REF = re.compile(r"(?<![\w./-])((?:references|scripts|assets|examples)/[\w./-]*\w\.\w+)")
ROOT_REF = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]*\w)")
SKILL_DIR_REF = re.compile(r"\$\{CLAUDE_SKILL_DIR\}/([\w./-]*\w)")
NAME_REF = re.compile(r"(?<![\w-])(arc-kit|arc-design|mgi-kit):([a-z][a-z-]*[a-z])")


def parse_frontmatter(text):
    lines = text.split("\n")
    if lines[0] != "---" or "---" not in lines[1:]:
        return None
    fields, key = {}, None
    for line in lines[1:lines.index("---", 1)]:
        m = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", line)
        if m:
            key, value = m.group(1), m.group(2).strip()
            fields[key] = "" if value in (">", "|", ">-", "|-") else value.strip("\"'")
        elif key and line.startswith((" ", "\t")):
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields


def components():
    for plugin in sorted(os.listdir(PLUGINS)):
        base = os.path.join(PLUGINS, plugin)
        skills = os.path.join(base, "skills")
        for name in sorted(os.listdir(skills)) if os.path.isdir(skills) else []:
            yield plugin, name, os.path.join(skills, name, "SKILL.md")
        agents = os.path.join(base, "agents")
        for file in sorted(os.listdir(agents)) if os.path.isdir(agents) else []:
            if file.endswith(".md"):
                yield plugin, file[:-3], os.path.join(agents, file)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def markdown_files():
    for dirpath, _, files in os.walk(PLUGINS):
        for file in files:
            if file.endswith(".md") and file != "CHANGELOG.md":
                yield os.path.join(dirpath, file)


class SkillLintTest(unittest.TestCase):
    def test_frontmatter_has_name_and_description(self):
        for plugin, name, path in components():
            fm = parse_frontmatter(read(path))
            self.assertIsNotNone(fm, f"skill-lint: no frontmatter in {path}")
            self.assertEqual(fm.get("name"), name, f"skill-lint: name mismatch in {path}")
            self.assertTrue(fm.get("description"), f"skill-lint: empty description in {path}")

    def test_description_budget(self):
        total = 0
        for plugin, name, path in components():
            desc = parse_frontmatter(read(path))["description"]
            total += len(desc)
            self.assertLessEqual(len(desc), DESCRIPTION_MAX, f"skill-lint: {plugin}:{name} description is {len(desc)} chars")
        self.assertLessEqual(total, CATALOG_MAX, f"skill-lint: catalog descriptions total {total} chars")

    def test_skill_body_budget(self):
        for plugin, name, path in components():
            size = os.path.getsize(path)
            self.assertLessEqual(size, SKILL_BYTES_MAX, f"skill-lint: {path} is {size} bytes")

    def test_referenced_paths_exist(self):
        for path in markdown_files():
            text = read(path)
            parts = os.path.relpath(path, PLUGINS).split(os.sep)
            plugin_root = os.path.join(PLUGINS, parts[0])
            skill_dir = os.path.join(plugin_root, *parts[1:3]) if parts[1] == "skills" else plugin_root
            for ref in PATH_REF.findall(text):
                if ROOT_REF.search(text) and any(m.endswith(ref) for m in ROOT_REF.findall(text)):
                    continue
                self.assertTrue(os.path.exists(os.path.join(skill_dir, ref)), f"skill-lint: {path} references missing {ref}")
            for ref in SKILL_DIR_REF.findall(text):
                self.assertTrue(os.path.exists(os.path.join(skill_dir, ref)), f"skill-lint: {path} references missing ${{CLAUDE_SKILL_DIR}}/{ref}")
            for ref in ROOT_REF.findall(text):
                self.assertTrue(os.path.exists(os.path.join(plugin_root, ref)), f"skill-lint: {path} references missing ${{CLAUDE_PLUGIN_ROOT}}/{ref}")

    def test_qualified_names_resolve(self):
        known = {f"{p}:{n}" for p, n, _ in components()}
        for path in list(markdown_files()) + [os.path.join(ROOT, "README.md")]:
            for plugin, name in NAME_REF.findall(read(path)):
                self.assertIn(f"{plugin}:{name}", known, f"skill-lint: {path} names unknown {plugin}:{name}")

    def test_every_component_is_listed(self):
        readme = read(os.path.join(ROOT, "README.md"))
        for plugin, name, path in components():
            listed = f"{plugin}:{name}" if "/skills/" in path else f"`{name}`"
            self.assertTrue(listed in readme or re.search(rf"^\|[^\n]*\| {re.escape(plugin)} \| `\${re.escape(name)}`(?: \([^\n]*\))? \|$", readme, re.M), f"skill-lint: README does not list {listed}")
            self.assertTrue(os.path.isfile(os.path.join(os.path.dirname(path), "agents", "openai.yaml")), f"skill-lint: {plugin}:{name} lacks discovery metadata")

    def test_version_matches_changelog(self):
        for plugin in sorted(os.listdir(PLUGINS)):
            manifest = json.loads(read(os.path.join(PLUGINS, plugin, "plugin.json")))
            m = re.search(r"^## \[(\d+\.\d+\.\d+)\]", read(os.path.join(PLUGINS, plugin, "CHANGELOG.md")), re.M)
            self.assertIsNotNone(m, f"skill-lint: no version heading in {plugin}/CHANGELOG.md")
            self.assertEqual(manifest["version"], m.group(1), f"skill-lint: {plugin} plugin.json and CHANGELOG disagree")


if __name__ == "__main__":
    unittest.main()
