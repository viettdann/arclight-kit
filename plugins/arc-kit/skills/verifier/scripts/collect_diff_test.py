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
