#!/usr/bin/env python3
import json
import os
import posixpath
import re
import shlex
import sys

from plugin_options import option

PREFIX = "destructive-guard:"
ARTIFACTS = {
    "node_modules", "dist", "build", ".next", "out", "coverage", "target", "bin", "obj",
    ".turbo", ".cache", "__pycache__", ".pytest_cache",
}
ROOTS = {"/", "/*", "~", "~/*", "$HOME", "$HOME/*", "..", "../*", "/.*", "~/.*", "$HOME/.*"}
SQL_CLIENTS = {"psql", "mysql", "mariadb", "sqlite3", "sqlcmd", "clickhouse-client", "cockroach", "duckdb"}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh"}
WRAPPERS = {
    "sudo": {
        "-u", "-g", "-p", "-C", "-U", "-h", "-r", "-t", "-T", "-D", "-R",
        "--user", "--group", "--prompt", "--close-from", "--other-user", "--host", "--role", "--type", "--command-timeout", "--chdir", "--chroot",
    },
    "doas": {"-u", "-C"},
    "env": {"-u", "-C", "-S", "--unset", "--chdir", "--split-string"},
    "nice": {"-n", "--adjustment"},
    "ionice": {"-c", "-n", "-p", "-P", "-u", "--class", "--classdata", "--pid", "--pgid", "--uid"},
    "exec": {"-a"},
    "time": {"-f", "-o", "--format", "--output"},
    "timeout": {"-k", "-s", "--kill-after", "--signal"},
    "stdbuf": {"-i", "-o", "-e", "--input", "--output", "--error"},
    "xargs": {
        "-a", "-d", "-E", "-I", "-L", "-n", "-P", "-s",
        "--arg-file", "--delimiter", "--max-args", "--max-procs", "--max-chars", "--max-lines", "--process-slot-var",
    },
    "nohup": set(), "command": set(), "builtin": set(), "busybox": set(),
}
CHECKED = {"rm", "git", "docker", "podman", "docker-compose", "kubectl", "terraform", "tofu", "chmod", "dd", "find", "rsync", "eval"} | SHELLS | set(WRAPPERS)
ASSIGN = re.compile(r"^[A-Za-z_]\w*=")
HEREDOC = re.compile(r"<<-?[ \t]*(['\"]?)\\?([A-Za-z_][\w.-]*)\1")
KEYWORDS = {"{", "}", "(", ")", "!", "if", "then", "else", "elif", "do", "while", "until"}
KEYWORD_HINT = re.compile(r"\b(rm|git|drop|truncate|delete|docker|kubectl|terraform|tofu|chmod|dd|mkfs\S*)\b", re.I)
IFS = re.compile(r"\$\{?IFS\b")
DECODE = r"(base64\s+(-\w*[dD]\w*|--decode)|xxd\s+(-\w*r\w*)|openssl\s+(enc\s+)?-?base64\s+-d)"
DECODE_PIPE = re.compile(DECODE + r"[^|;&\n]*\|\s*(sudo\s+)?(sh|bash|zsh|dash|ksh|eval|source)\b")
DECODE_SUBST = re.compile(r"\b(sh|bash|zsh|dash|ksh|eval|source)\b[^\n]*(\$\(|`|<\()[^\n]*" + DECODE)
SQL_DROP = re.compile(r"\bdrop\s+(table|database|schema)\b", re.I)
SQL_TRUNCATE = re.compile(r"\btruncate\s+(table\s+)?[\w\"`\[]", re.I)
SQL_DELETE = re.compile(r"\bdelete\s+from\b([^;]*)", re.I)
REDIRECT = re.compile(r"^\d*(>>?|<<?<?|>&|<&|&>>?)")


def guard_enabled():
    return option("destructive_guard_enabled", "false").lower() in ("true", "1", "yes", "on")


def skip_heredocs(cmd, i, words):
    # Bodies start after the newline at i and are data: no quote tracking, no segment splitting.
    j = i + 1
    for word in words:
        while j <= len(cmd):
            end = cmd.find("\n", j)
            end = len(cmd) if end < 0 else end
            line, j = cmd[j:end], end + 1
            if line.strip() == word:
                break
    return j - 1


def substitution(cmd, i, closer):
    depth, quote, heredocs = 1, None, []
    j = i
    while j < len(cmd):
        c = cmd[j]
        heredoc = None if quote or cmd.startswith("<<<", j) else HEREDOC.match(cmd, j)
        if not quote and cmd.startswith("<<<", j):
            j += 2
        elif heredoc:
            heredocs.append(heredoc.group(2))
            j = heredoc.end() - 1
        elif c == "\n" and heredocs and not quote:
            j = skip_heredocs(cmd, j, heredocs)
            heredocs = []
        elif quote:
            if c == "\\" and quote == '"':
                j += 1
            elif c == quote:
                quote = None
        elif c == "\\":
            j += 1
        elif c in "'\"":
            quote = c
        elif closer == "`" and c == "`":
            return cmd[i:j], j
        elif closer == ")" and c == "(":
            depth += 1
        elif closer == ")" and c == ")":
            depth -= 1
            if depth == 0:
                return cmd[i:j], j
        j += 1
    raise ValueError("unterminated substitution")


def body_substitutions(body):
    found, i = [], 0
    while i < len(body):
        c = body[i]
        if c == "\\":
            i += 1
        elif body.startswith("$(", i) or c == "`":
            inner, i = substitution(body, i + (1 if c == "`" else 2), "`" if c == "`" else ")")
            found.append(inner)
        i += 1
    return found


def feeds_shell(segments):
    return any(argv and posixpath.basename(argv[0]) in SHELLS for argv in (strip_wrappers(tokens(s)) for s in segments))


def split(cmd):
    segments, nested, buf, quote, i = [], [], [], None, 0
    heredocs, expands, line_start = [], False, 0
    while i < len(cmd):
        c, nxt = cmd[i], cmd[i + 1 : i + 2]
        heredoc = None if quote or cmd.startswith("<<<", i) else HEREDOC.match(cmd, i)
        if cmd.startswith("<<<", i) and not quote:
            buf.append("<<<")
            i += 2
        elif heredoc:
            heredocs.append(heredoc.group(2))
            expands = expands or not (heredoc.group(1) or "\\" in heredoc.group(0))
            buf.append(heredoc.group(0))
            i = heredoc.end() - 1
        elif c == "\n" and heredocs and not quote:
            segments.append("".join(buf))
            buf, end = [], skip_heredocs(cmd, i, heredocs)
            body = cmd[i + 1 : end + 1]
            # A heredoc piped into a shell on the same line is a script, not data.
            if feeds_shell(segments[line_start:]):
                nested.append(body)
            elif expands:
                nested.extend(body_substitutions(body))
            heredocs, expands, line_start, i = [], False, len(segments), end
        elif quote == "'":
            buf.append(c)
            if c == "'":
                quote = None
        elif c == "\\" and quote != "'":
            buf.append(cmd[i : i + 2])
            i += 1
        elif (c in "$<>" and nxt == "(") or c == "`":
            start = i + (1 if c == "`" else 2)
            inner, end = substitution(cmd, start, "`" if c == "`" else ")")
            nested.append(inner)
            buf.append(cmd[i : end + 1])
            i = end
        elif quote == '"':
            buf.append(c)
            if c == '"':
                quote = None
        elif c in "'\"":
            quote = c
            buf.append(c)
        elif c == "#" and (not buf or buf[-1][-1:].isspace()):
            while i + 1 < len(cmd) and cmd[i + 1] != "\n":
                i += 1
        elif c in ";|&\n()":
            segments.append("".join(buf))
            buf = []
            if c == "\n":
                line_start = len(segments)
        else:
            buf.append(c)
        i += 1
    if quote:
        raise ValueError("unbalanced quote")
    segments.append("".join(buf))
    for inner in nested:
        segments.extend(split(inner))
    return [s.strip() for s in segments if s.strip()]


def tokens(segment):
    try:
        argv = shlex.split(segment, posix=True)
    except ValueError:
        argv = segment.split()
    out, skip = [], False
    for tok in argv:
        if skip:
            skip = False
        elif REDIRECT.match(tok):
            skip = REDIRECT.sub("", tok) == ""
        else:
            out.append(tok)
    return out


def takes_value(flag, values):
    if flag.startswith("--"):
        return flag in values
    for k, letter in enumerate(flag[1:]):
        if f"-{letter}" in values:
            return k == len(flag) - 2
    return False


def strip_wrappers(argv):
    wrapped = False
    while argv:
        head = posixpath.basename(argv[0])
        if argv[0] in KEYWORDS or ASSIGN.match(argv[0]):
            argv = argv[1:]
            continue
        if head not in WRAPPERS:
            break
        wrapped, argv = True, argv[1:]
        while argv and argv[0].startswith("-") and argv[0] != "-":
            flag, argv = argv[0], argv[1:]
            if flag == "--":
                break
            if takes_value(flag, WRAPPERS[head]):
                argv = argv[1:]
        if head == "timeout":
            argv = argv[1:]
    # An unknown value flag can leave its value as the head; fall back to the first checked command after the wrapper.
    if wrapped and argv and posixpath.basename(argv[0]) not in CHECKED:
        rest = next((i for i, t in enumerate(argv) if posixpath.basename(t) in CHECKED), None)
        if rest is not None:
            return strip_wrappers(argv[rest:])
    return argv


def short_flag(args, letters):
    return any(re.match(rf"^-[A-Za-z]*[{letters}]", a) and not a.startswith("--") for a in args)


def split_flags(args):
    flags, positional, ended = [], [], False
    for a in args:
        if ended or not a.startswith("-") or a == "-":
            positional.append(a)
        elif a == "--":
            ended = True
        else:
            flags.append(a)
    return flags, positional


def is_root(target):
    t = target.replace("${HOME}", "$HOME")
    if t in ROOTS:
        return True
    norm = posixpath.normpath(t)
    return norm in ROOTS or bool(re.fullmatch(r"(\.\./)*\.\.(/\*)?", norm)) or norm in ("/.", "//")


def is_artifact(target):
    if "`" in target or any(c in target for c in "*?[{") or ".." in target.split("/"):
        return False
    t = target.rstrip("/")
    tmpdir = os.environ.get("TMPDIR", "").rstrip("/")
    tmps = ("/tmp", "/private/tmp", "/var/tmp") + (("$TMPDIR", "${TMPDIR}", tmpdir) if tmpdir else ())
    for tmp in tmps:
        if t.startswith(tmp + "/") and len(t) > len(tmp) + 1:
            return "$" not in t[len(tmp):]
    return not t.startswith(("/", "~", "$")) and "$" not in t and posixpath.basename(t) in ARTIFACTS


def check_rm(args):
    flags, targets = split_flags(args)
    if not (short_flag(flags, "rR") or "--recursive" in flags):
        return None
    roots = [t for t in targets if is_root(t)]
    if roots:
        return "deny", f"recursive rm of a root path ({roots[0]})"
    if targets and all(is_artifact(t) for t in targets):
        return None
    return "ask", "recursive rm outside the build-artifact allowlist"


def check_git(args):
    while args and args[0].startswith("-"):
        args = args[2:] if args[0] in ("-C", "-c", "--git-dir", "--work-tree", "--namespace") else args[1:]
    if not args:
        return None
    sub, rest = args[0], args[1:]
    flags, positional = split_flags(rest)
    if sub == "reset" and "--hard" in flags:
        return "ask", "git reset --hard discards uncommitted changes"
    if sub == "checkout" and ("--" in rest[:-1] or "." in positional or "--force" in flags or short_flag(flags, "f")):
        return "ask", "git checkout discards worktree changes"
    if sub == "restore" and not (({"--staged", "-S"} & set(flags)) and not ({"--worktree", "-W"} & set(flags))):
        return "ask", "git restore discards worktree changes"
    if sub == "clean" and (short_flag(flags, "f") or "--force" in flags) and not (short_flag(flags, "n") or "--dry-run" in flags):
        return "ask", "git clean deletes untracked files"
    if sub == "stash" and positional[:1] in (["drop"], ["clear"]):
        return "ask", f"git stash {positional[0]} deletes stashed work"
    if sub == "branch" and (short_flag(flags, "D") or ("--delete" in flags and ("--force" in flags or short_flag(flags, "f")))):
        return "ask", "git branch -D deletes an unmerged branch"
    return None


def check_docker(args):
    flags, positional = split_flags(args)
    pair = positional[:2]
    force = "--force" in flags or short_flag(flags, "f")
    if pair == ["system", "prune"]:
        return "ask", "docker system prune deletes images, containers, and networks"
    if pair[:1] == ["volume"] and pair[1:] in (["rm"], ["prune"], ["remove"]):
        return "ask", "docker volume removal deletes data"
    if pair[1:] == ["prune"]:
        return "ask", f"docker {pair[0]} prune deletes unused {pair[0]} objects"
    if pair[:1] == ["compose"] and "down" in positional and ("--volumes" in flags or short_flag(flags, "v")):
        return "ask", "docker compose down -v deletes named volumes"
    if (pair[:1] == ["rm"] or pair == ["container", "rm"]) and force:
        return "ask", "docker rm -f kills and removes containers"
    return None


def shell_script(args):
    has_c, i = False, 0
    while i < len(args):
        a = args[i]
        if not a.startswith(("-", "+")):
            break
        has_c = has_c or (a[0] == "-" and not a.startswith("--") and "c" in a[1:])
        i += 2 if a in ("-o", "+o", "-O", "+O") else 1
    return args[i] if has_c and i < len(args) else None


def check_find(args):
    execs_rm = any(a in ("-exec", "-execdir", "-ok", "-okdir") and posixpath.basename(b) == "rm" for a, b in zip(args, args[1:]))
    if "-delete" not in args and not execs_rm:
        return None
    paths = [a for a in args if a not in ("-H", "-L", "-P")]
    paths = paths[: next((i for i, a in enumerate(paths) if a.startswith(("-", "(", "!"))), len(paths))]
    roots = [p for p in paths if is_root(p)]
    if roots:
        return "deny", f"find deletes under a root path ({roots[0]})"
    return "ask", "find -delete or -exec rm deletes every match"


def check_argv(argv):
    argv = strip_wrappers(argv)
    if not argv:
        return []
    head, args = posixpath.basename(argv[0]), argv[1:]
    if head in SHELLS:
        script = shell_script(args)
        return check_command(script) if script is not None else []
    if head == "eval":
        return check_command(" ".join(args))
    if head == "rm":
        found = check_rm(args)
    elif head == "git":
        found = check_git(args)
    elif head in ("docker", "podman"):
        found = check_docker(args)
    elif head == "docker-compose":
        found = check_docker(["compose", *args])
    elif head == "find":
        found = check_find(args)
    elif head == "rsync" and any(a.startswith("--del") for a in args):
        found = "ask", "rsync --delete removes files missing from the source"
    elif head == "kubectl" and "delete" in args:
        found = "ask", "kubectl delete removes cluster resources"
    elif head in ("terraform", "tofu") and ("destroy" in args or "-destroy" in args):
        found = "ask", f"{head} destroy tears down infrastructure"
    elif head == "chmod" and (short_flag(args, "R") or "--recursive" in args) and {"777", "0777", "a+rwx", "ugo+rwx"} & set(args):
        found = "ask", "chmod -R 777 opens every file to everyone"
    elif head == "dd" and any(re.match(r"^of=/dev/(?!null$|zero$|stdout$|stderr$)", a) for a in args):
        found = "ask", "dd writes to a raw device"
    elif head.startswith("mkfs"):
        found = "ask", "mkfs formats a filesystem"
    else:
        found = None
    return [found] if found else []


def check_sql(cmd, argvs):
    if not any(posixpath.basename(t) in SQL_CLIENTS for argv in argvs for t in argv):
        return []
    found = []
    if SQL_DROP.search(cmd):
        found.append(("ask", "SQL DROP deletes database objects"))
    if SQL_TRUNCATE.search(cmd):
        found.append(("ask", "SQL TRUNCATE deletes every row"))
    if any(not re.search(r"\bwhere\b", m.group(1), re.I) for m in SQL_DELETE.finditer(cmd)):
        found.append(("ask", "SQL DELETE without WHERE deletes every row"))
    return found


def check_command(cmd):
    if IFS.search(cmd):
        return [("deny", "${IFS} word-splitting obfuscation")]
    if DECODE_PIPE.search(cmd) or DECODE_SUBST.search(cmd):
        return [("deny", "decoded payload executed by a shell")]
    try:
        segments = split(cmd)
    except ValueError as e:
        return [("deny", f"cannot parse a command with destructive keywords ({e})")] if KEYWORD_HINT.search(cmd) else []
    argvs = [tokens(s) for s in segments]
    found = check_sql(cmd, argvs)
    for argv in argvs:
        found += check_argv(argv)
    return found


def decide(decision, reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": f"{PREFIX} {reason}",
        }
    }))
    return 0


def main():
    try:
        return guard()
    except Exception as e:
        return decide("deny", f"internal error ({type(e).__name__}); refusing to run an unchecked command")


def guard():
    if not guard_enabled():
        return 0
    try:
        payload = json.loads(sys.stdin.read())
    except ValueError:
        return decide("deny", "unreadable hook payload; refusing to run an unchecked command")
    if not isinstance(payload, dict):
        return decide("deny", "unreadable hook payload; refusing to run an unchecked command")
    if payload.get("tool_name") not in (None, "Bash"):
        return 0
    cmd = (payload.get("tool_input") or {}).get("command")
    if not isinstance(cmd, str) or not cmd.strip():
        return decide("deny", "no command in the hook payload; refusing to run an unchecked command")
    found = check_command(cmd)
    denies = [r for d, r in found if d == "deny"]
    if denies:
        return decide("deny", f"blocked: {denies[0]}. Run it yourself outside Claude if intended")
    asks = list(dict.fromkeys(r for d, r in found if d == "ask"))
    if asks:
        return decide("ask", "; ".join(asks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
