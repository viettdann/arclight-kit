import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "agent-git-guard.py")
HOOKS = os.path.join(os.path.dirname(HERE), "hooks", "hooks.json")


def run(stdin):
    return subprocess.run([sys.executable, SCRIPT], input=stdin, capture_output=True, text=True)


def payload(command, agent="arc-kit:worker", tool="Bash"):
    data = {"tool_name": tool, "tool_input": {"command": command}}
    if agent is not None:
        data["agent_id"], data["agent_type"] = "a1", agent
    return json.dumps(data)


class AgentGitGuardTest(unittest.TestCase):
    def decision(self, command, **kw):
        r = run(payload(command, **kw))
        self.assertEqual(r.returncode, 0, r.stderr)
        if not r.stdout.strip():
            return "allow"
        out = json.loads(r.stdout)["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "PreToolUse")
        self.assertTrue(out["permissionDecisionReason"].startswith("agent-git-guard: "))
        self.assertIn("Blocked on", out["permissionDecisionReason"])
        return out["permissionDecision"]

    def expect(self, decision, *commands, **kw):
        for command in commands:
            with self.subTest(command=command):
                self.assertEqual(self.decision(command, **kw), decision)

    def test_read_only_git_allowed(self):
        self.expect(
            "allow",
            "git status --short",
            "git diff -- src/a.ts",
            "git --no-pager log --oneline -5",
            "git -C sub show HEAD:src/a.ts",
            "git blame -L 10,20 src/a.ts",
            "git grep -n foo",
            "git ls-files --others --exclude-standard",
            "git rev-parse HEAD",
            "git diff --stat && npm test",
            "git diff -Oorder.txt",
            "git log --oneline --grep git",
            "git grep -n git src",
            "grep -rn 'git stash' docs",
            "grep -rn GIT_DIR= src",
            "git cat-file -p HEAD:src/a.ts",
            "git ls-tree HEAD src",
            "git merge-base HEAD main",
            "git rev-list --count HEAD",
            "git branch --show-current",
            "git branch -a",
            "git branch",
            "git remote -v",
            "git reflog -5",
            "git config --get user.name",
            "git describe --tags",
            "find src -name '*.ts' -exec git log -1 {} ;",
            "find . -path ./.git -prune -o -name '*.ts' -print",
            "find . -name git-hooks",
            "git --git-dir=.git log -1",
            "HOME=/tmp npm test",
            "\"$VENV/bin/pytest\" -q",
            "python3 /tmp/x/snapshot.py diff /tmp/supervise-1 A",
            "git config --list",
        )

    def test_state_changing_git_denied(self):
        self.expect(
            "deny",
            "git stash",
            "git stash push -m x",
            "git stash pop",
            "git stash apply",
            "git stash list",
            "git reset --soft HEAD~1",
            "git reset src/a.ts",
            "git checkout -- src/a.ts",
            "git checkout main",
            "git switch -c tmp",
            "git restore src/a.ts",
            "git clean -fd",
            "git add src/a.ts",
            "git commit -m wip",
            "git rebase main",
            "git merge x",
            "git pull",
            "git push",
            "git cherry-pick abc",
            "git revert abc",
            "git rm src/a.ts",
            "git mv a b",
            "git worktree add /tmp/x",
            "git branch -D x",
            "git apply patch.diff",
        )

    def test_hidden_forms_denied(self):
        self.expect(
            "deny",
            "npm test; git stash",
            "cd src && git checkout -- .",
            "bash -c 'git stash'",
            "sh -lc \"git reset --hard\"",
            "env GIT_DIR=.git git stash",
            "timeout 10 git stash",
            "echo $(git stash)",
            "eval git stash",
            "git -C . stash",
            "git --git-dir=.git --work-tree=. reset --hard",
            "/usr/bin/git stash",
            "find . -name a.ts -exec git checkout -- {} +",
            "find . -exec git stash ;",
            "echo stash | xargs git",
            "watch -n1 git stash",
            "parallel git stash ::: a",
            "G=git; $G stash",
            "$(echo git) stash",
            "git --attr-source HEAD stash",
            "git branch -D x",
            "git branch new-branch",
            "git remote add o url",
            "git reflog expire --all",
            "git config user.name x",
            "git config --get x --unset",
            "git branch -- nb2",
            "git branch -v -- nb",
            "git reflog -- x",
            "find . -exec sh -c 'git stash' \\;",
            "watch -n1 'git stash'",
            "parallel 'git {}' ::: stash",
            "script -qc 'git stash' /dev/null",
            "flock /tmp/l -c 'git stash'",
            "chronic sh -c 'git stash'",
            "env -S 'git stash'",
            "env --split-string='git stash'",
            "$(printf gi)t stash",
            "\"$(printf 'g%s' it)\" stash",
            "alias g=git; g stash",
            "/usr/lib/git-core/git-stash",
            "git-stash push",
        )

    def test_read_only_escape_hatches_denied(self):
        self.expect(
            "deny",
            "git -c alias.st='!rm -rf src' st",
            "git -c core.pager='sh -c x' log",
            "git --config-env=core.pager=X log",
            "git diff --output=src/a.ts",
            "git diff --ext-diff",
            "git grep -Ovim foo",
            "git grep --open-files-in-pager=vim foo",
            "git grep -nOvim foo",
            "git grep --open-files=vim foo",
            "git grep --open=vim foo",
            "git diff --outp=src/a.ts",
            "git log --ext",
            "GIT_EXTERNAL_DIFF=./x.sh git diff",
            "env -u X GIT_EXTERNAL_DIFF=./x.sh git diff",
            "GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=alias.x GIT_CONFIG_VALUE_0='!sh' git x",
            "export GIT_PAGER='sh -c x'; git log",
            "export GIT_EXTERNAL_DIFF",
            "PAGER=x git log",
            "HOME=/tmp/evil git diff",
            "XDG_CONFIG_HOME=/tmp/evil git diff",
            "export HOME=/tmp/evil; git diff",
            "LESSOPEN='|x %s' git log",
        )

    def test_git_internals_denied(self):
        self.expect(
            "deny",
            "printf '[core]\\n\\tfsmonitor = ./x.sh\\n' >> .git/config",
            "sed -i s/a/b/ .git/config",
            "cp x .git/hooks/pre-commit",
            "cd .git && echo x >> config",
            "echo x >> ~/.gitconfig",
            "cat ~/.config/git/config",
        )

    def test_edit_tools_kept_out_of_git_files(self):
        for tool, path, decision in (
            ("Edit", "/repo/.git/config", "deny"),
            ("Write", ".git/hooks/pre-commit", "deny"),
            ("MultiEdit", "/home/u/.gitconfig", "deny"),
            ("Write", "/repo/src/a.ts", "allow"),
            ("Edit", "/repo/.gitignore", "allow"),
        ):
            with self.subTest(tool=tool, path=path):
                r = run(json.dumps({"tool_name": tool, "tool_input": {"file_path": path}, "agent_type": "arc-kit:worker"}))
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual("deny" if r.stdout.strip() else "allow", decision)

    def test_other_agents_and_main_thread_untouched(self):
        for agent in (None, "Explore", "arc-kit:test-runner", "general-purpose", "other:worker"):
            with self.subTest(agent=agent):
                self.assertEqual(self.decision("git stash", agent=agent), "allow")

    def test_non_git_and_non_bash_untouched(self):
        self.expect("allow", "rm -f build/out.txt", "cp /tmp/supervise-1/A/src/a.ts src/a.ts", "npx vitest run src/a.test.ts")
        self.assertEqual(self.decision("git stash", tool="Edit"), "allow")

    def test_bad_payload_is_silent(self):
        for stdin in ("", "not json", "[]", json.dumps({"agent_type": "arc-kit:worker", "tool_name": "Bash"})):
            with self.subTest(stdin=stdin):
                r = run(stdin)
                self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_unparseable_command_mentioning_git_denied(self):
        self.expect("deny", "git status '")

    def test_parser_failure_denies(self):
        with tempfile.TemporaryDirectory() as d:
            shutil.copy(SCRIPT, d)
            r = subprocess.run([sys.executable, os.path.join(d, "agent-git-guard.py")], input=payload("git status"), capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")


class HookCommandTest(unittest.TestCase):
    def setUp(self):
        with open(HOOKS) as f:
            hooks = json.load(f)["hooks"]["PreToolUse"]
        self.command = next(h["command"] for entry in hooks for h in entry["hooks"] if "agent-git-guard" in h["command"])

    def hook(self, agent, root):
        return subprocess.run(["sh", "-c", self.command], input=payload("git stash", agent=agent), capture_output=True, text=True, env={**os.environ, "CLAUDE_PLUGIN_ROOT": root})

    def test_guarded_agents_reach_the_guard(self):
        for agent in ("arc-kit:worker", "arc-kit:reviewer"):
            with self.subTest(agent=agent):
                r = self.hook(agent, os.path.dirname(HERE))
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn('"deny"', r.stdout)

    def test_other_agents_skip_python(self):
        # A missing script would fail loudly if Python ran, so silence proves the filter stopped first.
        for agent in (None, "Explore", "arc-kit:test-runner"):
            with self.subTest(agent=agent):
                r = self.hook(agent, "/nonexistent")
                self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))

    def test_guard_that_cannot_run_blocks(self):
        r = self.hook("arc-kit:worker", "/nonexistent")
        self.assertEqual(r.returncode, 2)
        self.assertIn("agent-git-guard", r.stderr)


if __name__ == "__main__":
    unittest.main()
