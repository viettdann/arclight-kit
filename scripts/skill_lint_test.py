import json
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGINS = os.path.join(ROOT, "plugins")
DESCRIPTION_MAX = 930
DESCRIPTION_MIN = 100
CATALOG_MAX = 14000
SKILL_BYTES_MAX = 8000
NAME_FORMAT = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TAG_LIKE = re.compile(r"<[A-Za-z/][^>]*>")
USE_WHEN = re.compile(r"\bUse (?:when|whenever|before|after)\b|\bTrigger (?:when|on)\b")
NOT_FOR = re.compile(r"\bNot for\b")
MD_LINK = re.compile(r"\]\((?!https?://|#|mailto:)([^)\s]+)\)")
PATH_REF = re.compile(r"(?<![\w./-])((?:references|scripts|assets|examples)/[\w./-]*\w\.\w+)")
ROOT_REF = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]*\w)")
SKILL_DIR_REF = re.compile(r"\$\{CLAUDE_SKILL_DIR\}/([\w./-]*\w)")
NAME_REF = re.compile(r"(?<![\w-])(arc-kit|arc-design|mgi-kit):([a-z][a-z-]*[a-z])")
REMOTE_EXEC = {
    "curl or wget piped to a shell": re.compile(r"\b(?:curl|wget)\b[^|\n]*\|\s*(?:sudo\s+)?(?:sh|bash|zsh|fish)\b", re.I),
    "eval of command output": re.compile(r"(?<![\w-])eval\s+[\"']?\$\("),
    "base64 decoded into an interpreter": re.compile(r"base64\s+(?:-d|--decode)[^|\n]*\|\s*(?:sh|bash|node|python3?)\b", re.I),
    "Invoke-Expression on downloaded content": re.compile(r"\b(?:Invoke-Expression|iex)\b.*\b(?:DownloadString|Invoke-WebRequest|iwr|irm)\b", re.I),
    "URL with a raw IP address": re.compile(r"https?://(?!127\.0\.0\.1\b|0\.0\.0\.0\b)(?:\d{1,3}\.){3}\d{1,3}\b"),
}
LINT_ALLOW = re.compile(r"skill-lint:\s*allow\s+\S")


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


def instruction_files():
    for plugin in sorted(os.listdir(PLUGINS)):
        for part in ("skills", "agents"):
            for dirpath, dirs, files in os.walk(os.path.join(PLUGINS, plugin, part)):
                dirs[:] = [d for d in dirs if d not in ("__pycache__", "node_modules")]
                for file in files:
                    if file.endswith((".md", ".py", ".sh", ".mjs", ".js", ".yml", ".yaml")) and not file.endswith("_test.py"):
                        yield os.path.join(dirpath, file)


class SkillLintTest(unittest.TestCase):
    def test_frontmatter_has_name_and_description(self):
        for plugin, name, path in components():
            fm = parse_frontmatter(read(path))
            self.assertIsNotNone(fm, f"skill-lint: no frontmatter in {path}")
            self.assertEqual(fm.get("name"), name, f"skill-lint: name mismatch in {path}")
            self.assertTrue(fm.get("description"), f"skill-lint: empty description in {path}")

    def test_name_format(self):
        for plugin, name, path in components():
            self.assertRegex(name, NAME_FORMAT, f"skill-lint: {plugin}:{name} is not lowercase words joined by single hyphens")
            self.assertLessEqual(len(name), 64, f"skill-lint: {plugin}:{name} name is over 64 chars")

    def test_description_budget(self):
        # The skill menu renders description and when_to_use together; agents are listed separately.
        total = 0
        for plugin, name, path in components():
            fm = parse_frontmatter(read(path))
            menu = len(fm["description"]) + len(fm.get("when_to_use", ""))
            self.assertLessEqual(menu, DESCRIPTION_MAX, f"skill-lint: {plugin}:{name} description and when_to_use are {menu} chars")
            if "/skills/" in path:
                total += menu
        self.assertLessEqual(total, CATALOG_MAX, f"skill-lint: skill menu totals {total} chars")

    def test_description_routes(self):
        for plugin, name, path in components():
            fm = parse_frontmatter(read(path))
            text = f"{fm['description']} {fm.get('when_to_use', '')}"
            self.assertIsNone(TAG_LIKE.search(text), f"skill-lint: {plugin}:{name} description has a tag-like <...>, which marketplace sync rejects")
            self.assertGreaterEqual(len(fm["description"]), DESCRIPTION_MIN, f"skill-lint: {plugin}:{name} description is too short to route on")
            if "/skills/" not in path or name in {"arc", "conventions", "handoff", "fresh-air"}:
                continue
            self.assertRegex(text, USE_WHEN, f"skill-lint: {plugin}:{name} description has no \"Use when\" trigger")
            self.assertRegex(text, NOT_FOR, f"skill-lint: {plugin}:{name} description has no \"Not for\" exclusion against its siblings")

    def test_skill_links_stay_inside_the_skill(self):
        for plugin, name, path in components():
            if "/skills/" not in path:
                continue
            for link in MD_LINK.findall(read(path)):
                target = link.split("#")[0]
                self.assertFalse(target.startswith(("/", "..")) or "/../" in target, f"skill-lint: {path} links outside its skill: {link}")
                self.assertLessEqual(target.count("/"), 1, f"skill-lint: {path} links more than one directory deep: {link}")

    def test_skill_local_anchors_exist(self):
        for _, _, path in components():
            text = read(path)
            headings = re.findall(r"^#{1,6} (.+)$", text, re.M)
            anchors = {re.sub(r"[^\w -]", "", heading.lower()).replace(" ", "-") for heading in headings}
            for anchor in re.findall(r"\]\(#([\w-]+)\)", text):
                self.assertIn(anchor, anchors, f"skill-lint: {path} has missing anchor #{anchor}")

    def test_marketplace_matches_plugins(self):
        from validate_plugins import validate
        errors, _ = validate()
        self.assertEqual(errors, [], "skill-lint: " + "; ".join(errors))

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

    def test_no_remote_code_execution(self):
        for path in instruction_files():
            for n, line in enumerate(read(path).splitlines(), 1):
                if LINT_ALLOW.search(line):
                    continue
                for what, pattern in REMOTE_EXEC.items():
                    self.assertIsNone(pattern.search(line), f"skill-lint: {path}:{n} has {what}; add `skill-lint: allow <reason>` on the line if intended")

    def test_version_matches_changelog(self):
        for plugin in sorted(os.listdir(PLUGINS)):
            manifest = json.loads(read(os.path.join(PLUGINS, plugin, "plugin.json")))
            m = re.search(r"^## \[(\d+\.\d+\.\d+)\]", read(os.path.join(PLUGINS, plugin, "CHANGELOG.md")), re.M)
            self.assertIsNotNone(m, f"skill-lint: no version heading in {plugin}/CHANGELOG.md")
            self.assertEqual(manifest["version"], m.group(1), f"skill-lint: {plugin} plugin.json and CHANGELOG disagree")


if __name__ == "__main__":
    unittest.main()
