#!/usr/bin/env python3
import importlib.util
import json
import os
import posixpath
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PREFIX = "agent-git-guard:"
AGENTS = {"arc-kit:worker", "arc-kit:reviewer"}
READ_ONLY = {
    "status", "diff", "log", "show", "blame", "grep", "ls-files", "ls-tree", "cat-file", "rev-parse", "rev-list",
    "merge-base", "describe", "shortlog", "show-ref", "for-each-ref", "name-rev",
}
# Read-only only in their listing forms; any other argument can create, delete, or rewrite something.
LISTING = {
    "branch": {"--show-current", "-a", "--all", "-r", "--remotes", "-v", "-vv", "--verbose", "-l", "--list", "--no-color"},
    "remote": {"-v", "--verbose"},
}
CONFIG_READS = {"--get", "--get-all", "--get-regexp", "-l", "--list"}
CONFIG_WRITES = {"--add", "--unset", "--unset-all", "--replace-all", "--rename-section", "--remove-section", "-e", "--edit"}
GLOBAL_WITH_VALUE = {"-C", "--git-dir", "--work-tree", "--namespace", "--attr-source", "--super-prefix", "--list-cmds"}
# Config overrides can turn a read-only subcommand into an arbitrary command through aliases, pagers, fsmonitor, or diff drivers.
CONFIG_FLAGS = {"-c", "--config-env", "--exec-path"}
GIT_ENV = re.compile(r"^(GIT_\w*|PAGER)(=|$)")
# These only matter in front of git: they point it at another global config or a pager preprocessor.
GIT_ENV_WITH_GIT = re.compile(r"^(HOME|XDG_CONFIG_HOME|LESSOPEN|LESSCLOSE)(=|$)")
DECLARES = {"export", "declare", "typeset", "readonly", "local"}
# Files under .git and git's config files; writing them rewires what read-only git runs.
GIT_PATH = re.compile(r"(^|[^\w.-])\.git/|(^|[^\w.-])\.gitconfig\b|(^|[^\w.-])\.config/git\b")
GIT_DIR = re.compile(r"(^|/)\.git/?$")
# Options that let a read-only subcommand write a file or launch a program; git accepts any unambiguous prefix of a long option.
WRITING_LONG = {"--output", "--ext-diff"}
GREP_PAGER_LONG = "--open-files-in-pager"
GREP_PAGER_SHORT = re.compile(r"^-[A-Za-z]*O")
GIT_WORD = re.compile(r"\bgit\b")
LAUNCHERS = {"find", "fd", "watch", "parallel", "flock", "entr", "unbuffer", "chronic", "setsid", "script", "strace", "ltrace"}
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def load_parser():
    spec = importlib.util.spec_from_file_location("destructive_guard", os.path.join(HERE, "destructive-guard.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def abbreviates(arg, option):
    name = arg.split("=")[0]
    return name.startswith("--") and len(name) > 3 and option.startswith(name)


def check_git(args):
    while args and args[0].startswith("-"):
        flag = args[0]
        if flag.split("=")[0] in CONFIG_FLAGS:
            return f"`git {flag}` (config override)"
        args = args[2:] if flag in GLOBAL_WITH_VALUE else args[1:]
    if not args:
        return "`git` without a subcommand (xargs or stdin can supply one)"
    sub, rest = args[0], args[1:]
    # Listing forms are judged on every argument: `git branch -- name` still creates a branch.
    positional = [a for a in rest if a != "--" and not a.startswith("-")]
    if sub == "reflog":
        return None if positional in ([], ["show"]) else f"`git {' '.join(args[:3])}`"
    if sub in LISTING:
        return None if not positional and all(a in LISTING[sub] for a in rest) else f"`git {' '.join(args[:3])}`"
    if sub == "config":
        flags = {a.split("=")[0] for a in rest}
        return None if flags & CONFIG_READS and not flags & CONFIG_WRITES else "`git config` other than --get or --list"
    if sub not in READ_ONLY:
        return f"`git {sub}`"
    options = rest[: rest.index("--")] if "--" in rest else rest
    for a in options:
        if any(abbreviates(a, o) for o in WRITING_LONG):
            return f"`git {sub} {a}`"
        if sub == "grep" and (abbreviates(a, GREP_PAGER_LONG) or GREP_PAGER_SHORT.match(a)):
            return f"`git grep {a}`"
    return None


def until_separator(argv, i):
    end = next((j for j in range(i, len(argv)) if argv[j] in (";", "+", ":::")), len(argv))
    return argv[i:end]


def sets_git_env(dg, argv, mentions_git):
    def matches(name):
        return GIT_ENV.match(name) or (mentions_git and GIT_ENV_WITH_GIT.match(name))
    if argv and argv[0] in DECLARES:
        return any(matches(a) for a in argv[1:])
    # Only assignments before a command count; `grep -rn GIT_DIR= src` is a search, not an override.
    git_at = next((i for i, t in enumerate(argv) if posixpath.basename(t) == "git"), None)
    if git_at is not None and any("=" in t and matches(t) for t in argv[:git_at]):
        return True
    for t in argv:
        if "=" in t and matches(t):
            return True
        if not (dg.ASSIGN.match(t) or posixpath.basename(t) in dg.WRAPPERS or t.startswith("-")):
            return False
    return False


def git_check(dg, mentions_git):
    def check(raw, argv):
        head = posixpath.basename(argv[0])
        if sets_git_env(dg, raw, mentions_git):
            return [("deny", "a GIT_*, PAGER, or git config location override")]
        if "$(" in argv[0] or "`" in argv[0] or (mentions_git and "$" in argv[0]):
            return [("deny", "a command whose name is a variable or substitution")]
        if head == "alias" and any(GIT_WORD.search(a) for a in argv[1:]):
            return [("deny", "an alias that runs git")]
        if head in ("cd", "pushd") and any(GIT_DIR.search(a) for a in argv[1:]):
            return [("deny", "a path inside .git or a git config file")]
        calls = []
        if head == "git":
            calls.append(until_separator(argv, 1))
        elif head.startswith("git-"):
            # git-core helpers such as git-stash run the subcommand directly.
            calls.append([head[4:], *until_separator(argv, 1)])
        found = []
        if head in LAUNCHERS:
            for i, tok in enumerate(argv[1:], 1):
                if posixpath.basename(tok) == "git":
                    calls.append(until_separator(argv, i + 1))
                elif GIT_WORD.search(tok) and any(c.isspace() for c in tok):
                    # A launcher argument holding a whole command line (`watch 'git stash'`, `sh -c '...'` after -exec).
                    found += dg.check_command(tok, check, None, GIT_WORD)
        found += [("deny", issue) for issue in map(check_git, calls) if issue]
        return found
    return check


def check_command(dg, cmd):
    # Checked on the raw text because the parser drops redirect targets (`>> .git/config`).
    if GIT_PATH.search(cmd):
        return ["a path inside .git or a git config file"]
    # destructive-guard's walker follows `bash -c`, `env -S`, eval, substitutions, and wrappers; this guard supplies only the git rules.
    found = dg.check_command(cmd, git_check(dg, bool(GIT_WORD.search(cmd))), None, GIT_WORD)
    return [reason for _, reason in found]


def check_path(path):
    return ["a path inside .git or a git config file"] if isinstance(path, str) and GIT_PATH.search(path) else []


def deny(agent, what):
    reason = (
        f"{PREFIX} {agent} may run only read-only git ({', '.join(sorted(READ_ONLY))}, and the listing forms of branch, remote, reflog, and config) and may not touch .git or git config files. Denied: {what}. "
        "Don't work around it with another command: put the command and what you needed it for under \"Blocked on\" in your report and stop; the supervisor decides."
    )
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}))
    return 0


def main():
    try:
        payload = json.loads(sys.stdin.read())
    except ValueError:
        return 0
    if not isinstance(payload, dict) or payload.get("agent_type") not in AGENTS:
        return 0
    agent = payload["agent_type"]
    tool, tool_input = payload.get("tool_name"), payload.get("tool_input") or {}
    if tool in EDIT_TOOLS:
        found = check_path(tool_input.get("file_path") or tool_input.get("notebook_path"))
        return deny(agent, found[0]) if found else 0
    cmd = tool_input.get("command")
    if tool not in (None, "Bash") or not isinstance(cmd, str):
        return 0
    try:
        found = check_command(load_parser(), cmd)
    except Exception as e:
        return deny(agent, f"a command the guard failed to check ({type(e).__name__})")
    return deny(agent, found[0]) if found else 0


if __name__ == "__main__":
    sys.exit(main())
