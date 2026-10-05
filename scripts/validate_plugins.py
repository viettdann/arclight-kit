#!/usr/bin/env python3
"""Validate this repository's Codex package conventions without third-party dependencies."""

import argparse
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LEGACY = re.compile(r"CLAUDE_|AskUserQuestion|subagent_type|model:\s*[\"']?sonnet|disable-model-invocation|argument-hint:")
EXPLICIT_ONLY = {"arc", "conventions", "fresh-air", "handoff"}
BUNDLED_PATH = re.compile(r"(?<![\w/$])((?:\.\./|\./|references/|scripts/|assets/|examples/)[\w./-]+\.(?:md|py|mjs))\b")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def inside(root, value):
    if not isinstance(value, str) or not value.startswith("./"):
        raise ValueError(f"expected ./-relative path: {value!r}")
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()) or not path.exists():
        raise ValueError(f"missing or escaping path: {value}")
    return path


def skill_metadata(path):
    text = path.read_text(encoding="utf-8")
    parts = text.split("---\n", 2)
    if len(parts) != 3 or parts[0]:
        raise ValueError("missing YAML frontmatter")
    fields = {}
    for line in parts[1].splitlines():
        key, sep, value = line.partition(":")
        if not sep or key not in {"name", "description", "license"} or key in fields:
            raise ValueError(f"unsupported or duplicate frontmatter field: {line}")
        value = value.strip()
        fields[key] = json.loads(value) if value.startswith('"') else value
    if not NAME.fullmatch(fields.get("name", "")) or fields["name"] != path.parent.name:
        raise ValueError("skill name must match its directory")
    description = fields.get("description", "")
    if not isinstance(description, str) or not 1 <= len(description) <= 930:
        raise ValueError("description must contain 1–930 characters")
    if LEGACY.search(text):
        raise ValueError("Claude-specific runtime instructions remain")
    return fields


def ui_metadata(path, skill_name):
    text = path.read_text(encoding="utf-8")
    fields = {}
    section = None
    for line in text.splitlines():
        if not line.strip():
            continue
        if line in {"interface:", "policy:"}:
            section = line[:-1]
            continue
        match = re.fullmatch(r"  ([a-z_]+): (.+)", line)
        if not match or section is None:
            raise ValueError(f"invalid UI metadata line: {line}")
        key, raw = match.groups()
        value = json.loads(raw)
        full_key = f"{section}.{key}"
        if full_key in fields:
            raise ValueError(f"duplicate UI metadata: {full_key}")
        fields[full_key] = value
    for key in ("display_name", "short_description", "default_prompt"):
        value = fields.get(f"interface.{key}")
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"missing interface.{key}")
    if f"${skill_name}" not in fields["interface.default_prompt"]:
        raise ValueError("default prompt must invoke its skill")
    if skill_name in EXPLICIT_ONLY and fields.get("policy.allow_implicit_invocation") is not False:
        raise ValueError(f"{skill_name} must require explicit invocation")


def validate(root=ROOT):
    root = root.resolve()
    errors, names, skill_count = [], set(), 0
    try:
        marketplace = read_json(root / ".agents/plugins/marketplace.json")
        if marketplace["name"] != "arclight-kit" or not marketplace["interface"]["displayName"]:
            raise ValueError("invalid marketplace identity")
        entries = marketplace["plugins"]
        if not entries:
            raise ValueError("marketplace has no plugins")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return [f"marketplace: {exc}"], 0
    for entry in entries:
        label = entry.get("name", "<unnamed>")
        try:
            if not NAME.fullmatch(label) or label in names:
                raise ValueError("invalid or duplicate plugin name")
            names.add(label)
            if entry["source"]["source"] != "local":
                raise ValueError("expected local marketplace source")
            base = inside(root, entry["source"]["path"])
            if base.name != label:
                raise ValueError("plugin directory/name mismatch")
            if entry["policy"] != {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}:
                raise ValueError("unexpected installation/authentication policy")
            if not entry.get("category"):
                raise ValueError("missing category")
            portable = read_json(base / "plugin.json")
            compat = read_json(base / ".codex-plugin/plugin.json")
            if portable.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
                raise ValueError("missing portable schema declaration")
            if portable["name"] != label or not re.fullmatch(r"\d+\.\d+\.\d+", portable["version"]):
                raise ValueError("invalid manifest name/version")
            extension = portable["extensions"]["com.openai"]
            expected = {k: v for k, v in portable.items() if k not in {"$schema", "extensions"}}
            expected.update({"skills": "./skills/", **extension})
            if compat != expected:
                raise ValueError("Codex fallback differs from portable identity/settings")
            interface = extension["interface"]
            if not interface.get("displayName") or not interface.get("shortDescription"):
                raise ValueError("missing plugin UI metadata")
            prompts = interface["defaultPrompt"]
            if not isinstance(prompts, list) or not 1 <= len(prompts) <= 3 or any(not isinstance(p, str) or not 1 <= len(p) <= 128 for p in prompts):
                raise ValueError("expected 1–3 starter prompts, each at most 128 characters")
            if "hooks" in extension:
                hook = read_json(inside(base, extension["hooks"]))
                handlers = hook["hooks"]["PostToolUse"]
                if len(handlers) != 1 or handlers[0]["matcher"] != "^apply_patch$":
                    raise ValueError("comment lint must target apply_patch")
                if len(handlers[0]["hooks"]) != 1:
                    raise ValueError("comment lint requires one command handler")
                for handler in handlers[0]["hooks"]:
                    if handler["type"] != "command" or '${PLUGIN_ROOT}/scripts/comment-lint.py' not in handler["command"]:
                        raise ValueError("invalid hook command")
                inside(base, "./scripts/comment-lint.py")
                starts = hook["hooks"].get("SessionStart", [])
                if starts:
                    if len(starts) != 1 or starts[0]["matcher"] != "^compact$" or len(starts[0]["hooks"]) != 1:
                        raise ValueError("arc reload must be one handler on compact")
                    handler = starts[0]["hooks"][0]
                    if handler["type"] != "command" or '${PLUGIN_ROOT}/scripts/arc-compact.py' not in handler["command"]:
                        raise ValueError("invalid arc reload command")
                    inside(base, "./scripts/arc-compact.py")
                guards = hook["hooks"].get("PreToolUse", [])
                if guards:
                    if len(guards) != 1 or guards[0]["matcher"] != "^Bash$" or len(guards[0]["hooks"]) != 1:
                        raise ValueError("destructive guard must be one handler on Bash")
                    handler = guards[0]["hooks"][0]
                    if handler["type"] != "command" or '${PLUGIN_ROOT}/scripts/destructive-guard.py' not in handler["command"] or "ARC_DESTRUCTIVE_GUARD_ENABLED" not in handler["command"]:
                        raise ValueError("invalid destructive guard command")
                    inside(base, "./scripts/destructive-guard.py")
                if set(hook["hooks"]) - {"PostToolUse", "SessionStart", "PreToolUse"}:
                    raise ValueError("unexpected hook event")
            skills = sorted(inside(base, compat["skills"]).glob("*/SKILL.md"))
            if not skills:
                raise ValueError("plugin has no skills")
            for skill in skills:
                try:
                    metadata = skill_metadata(skill)
                    ui_metadata(skill.parent / "agents/openai.yaml", metadata["name"])
                    skill_count += 1
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    errors.append(f"{skill.relative_to(root)}: {exc}")
            for doc in base.rglob("*.md"):
                if doc.name == "CHANGELOG.md":
                    continue
                text = doc.read_text(encoding="utf-8")
                if LEGACY.search(text):
                    errors.append(f"{doc.relative_to(root)}: legacy runtime instruction")
                for relative in set(BUNDLED_PATH.findall(text)) if doc.name == "SKILL.md" else ():
                    target = (doc.parent / relative).resolve()
                    if not target.is_relative_to(base.resolve()) or not target.is_file():
                        errors.append(f"{doc.relative_to(root)}: invalid bundled reference {relative}")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"{label}: {exc}")
    folders = {p.name for p in (root / "plugins").iterdir() if p.is_dir()}
    if folders != names:
        errors.append("marketplace entries do not match plugin directories")
    if list(root.glob(".claude-plugin/*")) or list((root / "plugins").glob("*/.claude-plugin/*")):
        errors.append("legacy Claude manifests remain")
    return errors, skill_count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    errors, count = validate(args.root.resolve())
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Validated Codex marketplace, manifests, hooks, metadata, and {count} skills.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
