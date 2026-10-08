import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "destructive-guard.py")
ON = {"CLAUDE_PLUGIN_OPTION_DESTRUCTIVE_GUARD_ENABLED": "true"}


def run(stdin, options=ON, cwd=None, tmpdir="/var/folders/xy/T"):
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE_PLUGIN_OPTION_") and k != "TMPDIR"}
    env.update(options or {})
    if tmpdir is not None:
        env["TMPDIR"] = tmpdir
    return subprocess.run([sys.executable, SCRIPT], input=stdin, capture_output=True, text=True, env=env, cwd=cwd)


def bash(command, **kw):
    return run(json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}), **kw)


class DestructiveGuardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root)

    def decision(self, command, cwd=None, **kw):
        r = bash(command, cwd=cwd or self.root, **kw)
        self.assertEqual(r.returncode, 0, r.stderr)
        if not r.stdout.strip():
            return "allow"
        out = json.loads(r.stdout)["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "PreToolUse")
        self.assertTrue(out["permissionDecisionReason"].startswith("destructive-guard: "))
        return out["permissionDecision"]

    def expect(self, decision, *commands, cwd=None, **kw):
        for command in commands:
            with self.subTest(command=command):
                self.assertEqual(self.decision(command, cwd, **kw), decision)

    def test_disabled_is_silent(self):
        for options in (None, {"CLAUDE_PLUGIN_OPTION_DESTRUCTIVE_GUARD_ENABLED": "false"}, {"CLAUDE_PLUGIN_OPTION_destructive_guard_enabled": "true"}):
            r = bash("rm -rf /", options=options)
            self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))

    def test_uppercase_option_name_enables(self):
        for value in ("true", "1", "YES", " on "):
            with self.subTest(value=value):
                out = json.loads(bash("rm -rf /", options={"CLAUDE_PLUGIN_OPTION_DESTRUCTIVE_GUARD_ENABLED": value}).stdout)
                self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_hook_command_gates_on_the_same_values(self):
        with open(os.path.join(HERE, "..", "hooks", "hooks.json"), encoding="utf-8") as f:
            command = json.load(f)["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        stdin = json.dumps({"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}})
        for value, expected in (("true", "deny"), ("1", "deny"), ("Yes", "deny"), ("ON", "deny"), (" tRuE ", "deny"), ("false", ""), ("", ""), ("true x", ""), ("*", "")):
            with self.subTest(value=value):
                env = {**os.environ, "CLAUDE_PLUGIN_ROOT": os.path.dirname(HERE), "CLAUDE_PLUGIN_OPTION_DESTRUCTIVE_GUARD_ENABLED": value}
                r = subprocess.run(["sh", "-c", command], input=stdin, capture_output=True, text=True, env=env)
                got = json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"] if r.stdout.strip() else ""
                self.assertEqual((r.returncode, got), (0, expected), r.stderr)

    def test_internal_error_denies(self):
        sys.path.insert(0, HERE)
        spec = importlib.util.spec_from_file_location("destructive_guard", SCRIPT)
        guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard)
        stdin = io.StringIO(json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}}))
        out = io.StringIO()
        with mock.patch.dict(os.environ, ON), mock.patch.object(guard, "check_command", side_effect=RuntimeError("boom")), \
                mock.patch.object(sys, "stdin", stdin), redirect_stdout(out):
            self.assertEqual(guard.main(), 0)
        self.assertEqual(json.loads(out.getvalue())["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_malformed_payload_denies(self):
        for stdin in ("not json", "[]", json.dumps({"tool_name": "Bash", "tool_input": {}})):
            with self.subTest(stdin=stdin):
                out = json.loads(run(stdin).stdout)["hookSpecificOutput"]
                self.assertEqual(out["permissionDecision"], "deny")

    def test_other_tool_ignored(self):
        self.assertEqual(run(json.dumps({"tool_name": "Read", "tool_input": {}})).stdout, "")

    def test_rm_root_denies(self):
        self.expect(
            "deny",
            "rm -rf /", "rm -fr /*", "rm -r -f ~", "rm --recursive --force $HOME", "sudo rm -Rf ${HOME}/",
            "rm -rf ..", "rm -rf ../..", "sudo -u root rm -rf /", "xargs -I {} rm -rf /", 'rm -rf "/"', "rm -rf --no-preserve-root /", "rm -rf build /",
        )

    def test_rm_other_recursive_asks(self):
        self.expect("ask", "rm -rf src", "rm -r docs", "rm -rf node_modules src", "rm -rf /tmp", "find . | xargs rm -rf", "rm -rf ../node_modules")

    def test_rm_artifacts_allowed(self):
        self.expect(
            "allow",
            "rm -rf node_modules", "rm -rf dist build .next out coverage", "rm -rf web/node_modules/",
            "rm -rf target bin obj .turbo .cache __pycache__ .pytest_cache", "rm -rf /tmp/scratch",
            "rm -rf $TMPDIR/x", "rm -rf /var/folders/xy/T/run1", "rm file.txt", "rm -f a.log",
        )

    def test_artifact_names_only_count_for_relative_paths(self):
        self.expect(
            "ask",
            "rm -rf /usr/bin", "rm -rf /bin", "rm -rf ~/bin", "rm -rf ~/.cache", "rm -rf /usr/lib/node_modules",
            "rm -rf /opt/app/out", "rm -rf $HOME/node_modules", "rm -rf $X/dist",
        )

    def test_tmp_paths_need_a_literal_suffix_and_a_real_tmpdir(self):
        self.expect("ask", "rm -rf /tmp/$X", "rm -rf /tmp/${X}/y", "rm -rf $TMPDIR/$X", "rm -rf /tmp/a/$(id -u)")
        self.expect("ask", "rm -rf $TMPDIR/x", "rm -rf ${TMPDIR}/x", tmpdir=None)
        self.expect("ask", "rm -rf $TMPDIR/x", tmpdir="")

    def test_shell_c_flag_variants_check_the_script(self):
        self.expect("deny", "bash -lc 'rm -rf /'", "sh -ec 'rm -rf /'", "bash -xc 'rm -rf /'", "bash -c -- 'rm -rf /'", "bash -o pipefail -c 'rm -rf /'")
        self.expect("allow", "bash -lc 'ls'", "bash script.sh -c 'rm -rf /'")

    def test_wrapper_options_do_not_hide_the_command(self):
        self.expect(
            "deny",
            "timeout -k 5 60 rm -rf /", "timeout -s KILL 5 rm -rf /", "timeout --signal=KILL 5 rm -rf /", "timeout --signal KILL 5 rm -rf /",
            "exec -a foo rm -rf /", "ionice -c 3 rm -rf /", "stdbuf -o L rm -rf /", "xargs -d x rm -rf /", "sudo -s rm -rf /",
            "busybox rm -rf /", "sudo -Eu root rm -rf /", "nice -n 5 timeout 10 rm -rf /", "env -i PATH=/bin rm -rf /", "env -S 'rm -rf /'", "env --split-string='rm -rf /'",
            "sudo --unknown-flag val rm -rf /", "sudo -u git rm -rf /", "sudo -Eu git rm -rf /", "exec -a git rm -rf /",
        )
        self.expect("allow", "timeout 5 ls", "sudo apt install git", "xargs -n1 echo")

    def test_pushes_pass(self):
        self.expect(
            "allow",
            "git push origin main", "git push --force origin main", "git push -f origin master", "git push origin +main",
            "git push --force-with-lease origin HEAD:main", "git push --mirror", "git push origin --delete main", "git push --force",
        )

    def test_obfuscation_denies(self):
        self.expect(
            "deny",
            "rm${IFS}-rf${IFS}/", "echo cm0gLXJmIC8= | base64 -d | sh", "echo x | xxd -r -p | bash",
            'eval "$(echo cm0= | base64 --decode)"',
        )

    def test_git_discard_asks(self):
        self.expect(
            "ask",
            "git reset --hard HEAD~1", "git checkout -- .", "git checkout .", "git restore src/a.ts", "git clean -fdx",
            "git stash drop", "git stash clear", "git branch -D feature", "git -C repo reset --hard",
        )
        self.expect("allow", "git checkout -b feature", "git restore --staged a.ts", "git clean -n", "git stash list", "git branch -d done")

    def test_sql_asks(self):
        self.expect(
            "ask",
            'psql -c "DROP TABLE users"', "mysql -e 'drop database app'", 'psql -c "truncate orders"',
            'psql -c "DELETE FROM users"', 'echo "drop schema s cascade" | psql', 'docker exec db psql -c "Drop Table x"',
        )
        self.expect("allow", 'psql -c "DELETE FROM users WHERE id = 1"', 'psql -c "select 1"', 'git commit -m "drop table docs"')

    def test_infra_asks(self):
        self.expect(
            "ask",
            "docker system prune -af", "docker volume rm data", "docker volume prune", "docker rm -f web", "kubectl delete pod x",
            "terraform destroy", "chmod -R 777 .", "dd if=img of=/dev/sda", "mkfs.ext4 /dev/sdb1",
        )
        self.expect(
            "ask",
            "docker compose down -v", "docker compose -f dev.yml down --volumes", "docker-compose down -v", "docker image prune -a",
            "docker container prune", "docker network prune", "docker builder prune", "rsync -a --delete src/ dst/", "rsync -a --delete-after a b",
        )
        self.expect("allow", "docker compose down", "docker-compose up -d", "rsync -a src/ dst/")
        self.expect("allow", "docker rm web", "kubectl get pods", "terraform plan", "chmod 755 a.sh", "dd if=/dev/zero of=/dev/null")

    def test_compound_segments_checked(self):
        self.expect(
            "deny",
            'git commit -m "x" && rm -rf /', "ls; rm -rf ~", "true || rm -rf /", "echo ok\nrm -rf /",
            "echo $(rm -rf /)", "echo `rm -rf /`", 'git commit -m "$(rm -rf /)"', "bash -c 'rm -rf /'",
            "(cd x && rm -rf ..)", "rm -rf node_modules && rm -rf /",
        )
        self.expect("ask", "npm test | tee log && git reset --hard")

    def test_quoted_text_does_not_trigger(self):
        self.expect(
            "allow",
            'git commit -m "drop table docs"', 'git commit -m "rm -rf / is dangerous"', "echo 'git reset --hard'",
            'git commit -m "x && rm -rf /"', "grep -r 'DELETE FROM' src",
        )

    def test_find_delete(self):
        self.expect("deny", "find / -delete", "find ~ -name x -delete", "find / -exec rm -rf {} \\;", "find -L / -delete", "sudo find $HOME -delete")
        self.expect("ask", "find . -name '*.pyc' -delete", "find src -type f -exec rm {} +", "find -delete")
        self.expect("allow", "find . -name '*.py'", "find / -name passwd")

    def test_heredoc_body_is_data(self):
        self.expect(
            "allow",
            "git commit -m \"$(cat <<'EOF'\nfix: don't crash\nEOF\n)\"",
            "cat > notes.txt <<'EOF'\ngit push -f origin main\nEOF",
            "gh pr create --body \"$(cat <<'EOF'\n- user's flow\nEOF\n)\"",
            "cat <<-EOF > a\n\trm -rf /\n\tEOF\necho done",
            "cat <<<'rm -rf /'",
            "cat <<EOF\ndon't $HOME\nEOF", "cat <<'EOF'\n$(rm -rf /)\nEOF", "cat <<\\EOF\n`rm -rf /`\nEOF",
            "echo \"$(tr a-z A-Z <<<git\n)\"",
        )
        self.expect("deny", "cat <<EOF\n$(rm -rf /)\nEOF", "cat <<\"EOF\" <<X\nok\nEOF\n`rm -rf ~`\nX", "cat <<<git\nrm -rf /", "cat > notes.txt <<'EOF'\nhello\nEOF\nrm -rf /", "git commit -m \"$(cat <<'EOF'\nx\nEOF\n)\" && rm -rf /")

    def test_heredoc_fed_to_a_shell_is_checked(self):
        self.expect("deny", "bash <<'EOF'\nrm -rf /\nEOF", "cat <<EOF | sudo sh\nrm -rf ~\nEOF")
        self.expect("ask", "psql <<'EOF'\nDROP TABLE users;\nEOF")

    def test_unparseable_with_keyword_denies(self):
        self.expect("deny", 'rm -rf "/')
        self.expect("allow", 'echo "unterminated')


if __name__ == "__main__":
    unittest.main()
