import os
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "collect-diff.sh")
GIT_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@t",
}


class CollectDiffTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.tmp = os.path.join(self.root, "tmp")
        self.repo = os.path.join(self.root, "repo")
        os.makedirs(self.tmp)
        os.makedirs(self.repo)
        self.env = {**os.environ, **GIT_ENV, "TMPDIR": self.tmp}

    def tearDown(self):
        shutil.rmtree(self.root)

    def git(self, *args, cwd=None):
        subprocess.run(["git", *args], cwd=cwd or self.repo, env=self.env, check=True, capture_output=True)

    def write(self, name, content, cwd=None):
        path = os.path.join(cwd or self.repo, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def init_repo(self):
        self.git("init", "-q")
        self.write("a.txt", "one\n")
        self.write("other.txt", "keep\n")
        self.git("add", ".")
        self.git("commit", "-qm", "init")

    def run_script(self, *args, cwd=None):
        return subprocess.run(["sh", SCRIPT, *args], cwd=cwd or self.repo, env=self.env, capture_output=True, text=True)

    def diff_of(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        with open(result.stdout.strip(), encoding="utf-8") as f:
            return f.read()

    def test_uncommitted_change_in_scope_only(self):
        self.init_repo()
        self.write("a.txt", "two\n")
        self.write("other.txt", "foreign\n")
        diff = self.diff_of(self.run_script("a.txt"))
        self.assertIn("+two", diff)
        self.assertNotIn("foreign", diff)

    def test_untracked_directory_lists_every_file(self):
        self.init_repo()
        self.write("newdir/x.txt", "x\n")
        self.write("newdir/y.txt", "y\n")
        diff = self.diff_of(self.run_script("newdir"))
        self.assertIn("newdir/x.txt", diff)
        self.assertIn("newdir/y.txt", diff)

    def test_base_covers_committed_and_uncommitted(self):
        self.init_repo()
        self.write("a.txt", "committed\n")
        self.git("commit", "-qam", "session")
        self.write("a.txt", "committed\nuncommitted\n")
        diff = self.diff_of(self.run_script("--base", "HEAD~1", "a.txt"))
        self.assertIn("+committed", diff)
        self.assertIn("+uncommitted", diff)

    def test_clean_tree_diffs_unpushed_commits(self):
        self.init_repo()
        remote = os.path.join(self.root, "remote.git")
        self.git("init", "-q", "--bare", remote, cwd=self.root)
        self.git("remote", "add", "origin", remote)
        self.git("push", "-qu", "origin", "HEAD")
        self.write("a.txt", "unpushed\n")
        self.git("commit", "-qam", "local")
        diff = self.diff_of(self.run_script("."))
        self.assertIn("+unpushed", diff)

    def test_dirty_tree_includes_unpushed_commits(self):
        self.init_repo()
        remote = os.path.join(self.root, "remote.git")
        self.git("init", "-q", "--bare", remote, cwd=self.root)
        self.git("remote", "add", "origin", remote)
        self.git("push", "-qu", "origin", "HEAD")
        self.write("a.txt", "unpushed\n")
        self.git("commit", "-qam", "local")
        self.write("other.txt", "dirty\n")
        diff = self.diff_of(self.run_script("."))
        self.assertIn("+unpushed", diff)
        self.assertIn("+dirty", diff)
        self.assertNotIn("-unpushed", diff)

    def test_dirty_tree_up_to_date_with_upstream_diffs_head(self):
        self.init_repo()
        remote = os.path.join(self.root, "remote.git")
        self.git("init", "-q", "--bare", remote, cwd=self.root)
        self.git("remote", "add", "origin", remote)
        self.git("push", "-qu", "origin", "HEAD")
        self.write("a.txt", "dirty\n")
        diff = self.diff_of(self.run_script("a.txt"))
        self.assertIn("-one", diff)
        self.assertIn("+dirty", diff)

    def test_mid_merge_warns(self):
        self.init_repo()
        self.git("checkout", "-qb", "side")
        self.write("a.txt", "side\n")
        self.git("commit", "-qam", "side")
        self.git("checkout", "-q", "-")
        self.write("a.txt", "main\n")
        self.git("commit", "-qam", "main")
        subprocess.run(["git", "merge", "side"], cwd=self.repo, env=self.env, capture_output=True)
        result = self.run_script("a.txt")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("warning: a merge is in progress", result.stderr)
        self.assertNotIn("warning", result.stdout)

    def diverge(self):
        self.init_repo()
        self.git("checkout", "-qb", "side")
        self.write("a.txt", "side\n")
        self.git("commit", "-qam", "side")
        self.git("checkout", "-q", "-")
        self.write("a.txt", "main\n")
        self.git("commit", "-qam", "main")

    def assertWarns(self, op):
        result = self.run_script("a.txt")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"warning: {op} is in progress", result.stderr)

    def test_mid_rebase_warns(self):
        self.diverge()
        subprocess.run(["git", "rebase", "--merge", "side"], cwd=self.repo, env=self.env, capture_output=True)
        self.assertTrue(os.path.isdir(os.path.join(self.repo, ".git", "rebase-merge")))
        self.assertWarns("a rebase")

    def test_mid_cherry_pick_warns(self):
        self.diverge()
        subprocess.run(["git", "cherry-pick", "side"], cwd=self.repo, env=self.env, capture_output=True)
        self.assertWarns("a cherry-pick")

    def test_mid_am_warns_as_am(self):
        self.diverge()
        patch = os.path.join(self.root, "side.patch")
        with open(patch, "w", encoding="utf-8") as f:
            subprocess.run(["git", "format-patch", "-1", "side", "--stdout"], cwd=self.repo, env=self.env, stdout=f, check=True)
        subprocess.run(["git", "am", "-3", patch], cwd=self.repo, env=self.env, capture_output=True)
        self.assertWarns("an am")

    def test_clean_state_has_no_warning(self):
        self.init_repo()
        self.write("a.txt", "two\n")
        self.assertNotIn("warning", self.run_script("a.txt").stderr)

    def test_repo_without_commits(self):
        self.git("init", "-q")
        self.write("staged.txt", "s\n")
        self.git("add", "staged.txt")
        self.write("loose.txt", "l\n")
        diff = self.diff_of(self.run_script("."))
        self.assertIn("+s", diff)
        self.assertIn("+l", diff)

    def test_outside_git_whole_files(self):
        plain = os.path.join(self.root, "plain")
        self.write("dir/f.txt", "content\n", cwd=plain)
        diff = self.diff_of(self.run_script("dir", cwd=plain))
        self.assertIn("+content", diff)

    def test_empty_diff_exits_2_and_leaves_no_file(self):
        self.init_repo()
        result = self.run_script("a.txt")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(os.listdir(self.tmp), [])

    def test_bad_base_fails(self):
        self.init_repo()
        result = self.run_script("--base", "nope", "a.txt")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(os.listdir(self.tmp), [])

    def test_no_paths_fails(self):
        self.assertEqual(self.run_script().returncode, 64)


if __name__ == "__main__":
    unittest.main()
