import os
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snapshot.py")


def sh(cwd, *cmd):
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


class SnapshotTest(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.repo)
        sh(self.repo, "git", "init", "-q")
        sh(self.repo, "git", "config", "user.email", "t@t")
        sh(self.repo, "git", "config", "user.name", "t")
        for name in ("src/a.ts", "src/b.ts", "user.ts"):
            write(os.path.join(self.repo, name), "base\n")
        sh(self.repo, "git", "add", "-A")
        sh(self.repo, "git", "commit", "-qm", "init")
        # The user's uncommitted work, in a file the run will own and in one it won't, with awkward names.
        write(os.path.join(self.repo, "src/a.ts"), "base\nuser edit\n")
        write(os.path.join(self.repo, "user.ts"), "base\nuser edit\n")
        write(os.path.join(self.repo, "notes é x.md"), "draft\n")

    def run_script(self, *args, cwd=None):
        return subprocess.run([sys.executable, SCRIPT, *args], cwd=cwd or self.repo, capture_output=True, text=True)

    def take(self, cwd=None):
        r = self.run_script("take", cwd=cwd)
        self.assertEqual(r.returncode, 0, r.stderr)
        run = r.stdout.strip()
        self.addCleanup(shutil.rmtree, run, True)
        return run

    def test_clean_when_only_owned_files_change(self):
        run = self.take()
        self.assertEqual(self.run_script("backup", run, "A", "src/a.ts", "src/new.ts").returncode, 0)
        write(os.path.join(self.repo, "src/a.ts"), "base\nuser edit\nworker edit\n")
        write(os.path.join(self.repo, "src/new.ts"), "new\n")
        r = self.run_script("check", run)
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "clean"))

    def test_foreign_change_stray_head_and_stash_are_reported(self):
        run = self.take()
        self.run_script("backup", run, "A", "src/a.ts")
        write(os.path.join(self.repo, "user.ts"), "clobbered\n")
        write(os.path.join(self.repo, "src/b.ts"), "stray\n")
        os.remove(os.path.join(self.repo, "notes é x.md"))
        r = self.run_script("check", run)
        self.assertEqual(r.returncode, 1)
        self.assertIn("foreign-changed user.ts", r.stdout)
        self.assertIn("foreign-changed notes é x.md", r.stdout)
        self.assertIn("stray src/b.ts", r.stdout)
        sh(self.repo, "git", "stash", "-q")
        r = self.run_script("check", run)
        self.assertIn("stash-changed 0 -> 1 entries", r.stdout)

    def test_head_moved(self):
        run = self.take()
        sh(self.repo, "git", "commit", "-qm", "x", "--allow-empty")
        self.assertIn("head-moved", self.run_script("check", run).stdout)

    def test_take_from_subdirectory_covers_whole_repo(self):
        run = self.take(cwd=os.path.join(self.repo, "src"))
        write(os.path.join(self.repo, "user.ts"), "clobbered\n")
        self.assertIn("foreign-changed user.ts", self.run_script("check", run).stdout)

    def test_backup_keeps_uncommitted_state_and_diff_shows_only_the_worker(self):
        run = self.take()
        dest = self.run_script("backup", run, "A", "src/a.ts", "src/new.ts").stdout.strip()
        with open(os.path.join(dest, "src/a.ts")) as f:
            self.assertEqual(f.read(), "base\nuser edit\n")
        self.assertFalse(os.path.exists(os.path.join(dest, "src/new.ts")))
        write(os.path.join(self.repo, "src/a.ts"), "base\nuser edit\nworker edit\n")
        write(os.path.join(self.repo, "src/new.ts"), "new\n")
        out = self.run_script("diff", run, "A").stdout
        self.assertIn("+worker edit", out)
        self.assertNotIn("+user edit", out)
        self.assertIn("--- /dev/null", out)
        self.assertIn("+new", out)

    def test_backup_twice_keeps_the_first_copy_or_absence(self):
        run = self.take()
        self.run_script("backup", run, "A", "src/a.ts", "src/new.ts")
        write(os.path.join(self.repo, "src/a.ts"), "worker edit\n")
        write(os.path.join(self.repo, "src/new.ts"), "worker\n")
        dest = self.run_script("backup", run, "A", "src/a.ts", "src/new.ts").stdout.strip()
        with open(os.path.join(dest, "src/a.ts")) as f:
            self.assertEqual(f.read(), "base\nuser edit\n")
        self.assertIn("--- /dev/null", self.run_script("diff", run, "A").stdout)

    def test_retake_into_same_run(self):
        run = self.take()
        write(os.path.join(self.repo, "user.ts"), "user again\n")
        self.assertEqual(self.run_script("take", "--run", run).stdout.strip(), run)
        self.assertEqual(self.run_script("check", run).stdout.strip(), "clean")

    def test_outside_git(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        write(os.path.join(d, "a.txt"), "one\n")
        r = self.run_script("take", cwd=d)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("not a git repository", r.stderr)
        run = r.stdout.strip()
        self.addCleanup(shutil.rmtree, run, True)
        self.assertEqual(self.run_script("check", run, cwd=d).stdout.strip(), "skipped: not a git repository")
        self.run_script("backup", run, "A", "a.txt", cwd=d)
        write(os.path.join(d, "a.txt"), "two\n")
        self.assertIn("+two", self.run_script("diff", run, "A", cwd="/").stdout)

    def test_file_handed_from_another_group_starts_from_its_current_state(self):
        run = self.take()
        self.run_script("backup", run, "A", "src/b.ts")
        write(os.path.join(self.repo, "src/b.ts"), "base\nfrom A\n")
        self.run_script("backup", run, "B", "src/b.ts")
        write(os.path.join(self.repo, "src/b.ts"), "base\nfrom A\nfrom B\n")
        out = self.run_script("diff", run, "B").stdout
        self.assertIn("+from B", out)
        self.assertNotIn("+from A", out)

    def test_directory_rejected(self):
        run = self.take()
        r = self.run_script("backup", run, "A", "src")
        self.assertEqual(r.returncode, 2)
        self.assertIn("is a directory", r.stderr)

    def test_diff_marks_missing_newline_binary_and_non_utf8(self):
        run = self.take()
        self.run_script("backup", run, "A", "src/a.ts", "bin.dat", "latin.txt")
        with open(os.path.join(self.repo, "src/a.ts"), "w") as f:
            f.write("base\nuser edit\nno newline")
        with open(os.path.join(self.repo, "bin.dat"), "wb") as f:
            f.write(b"\x00\x01")
        with open(os.path.join(self.repo, "latin.txt"), "wb") as f:
            f.write(b"caf\xe9\n")
        r = subprocess.run([sys.executable, SCRIPT, "diff", run, "A"], cwd=self.repo, capture_output=True, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(b"+no newline\n\\ No newline at end of file\n", r.stdout)
        self.assertIn(b"Binary files /dev/null and b/bin.dat differ", r.stdout)
        self.assertIn(b"+caf\xe9", r.stdout)

    def test_absolute_path_through_symlink(self):
        link = tempfile.mktemp()
        os.symlink(self.repo, link)
        self.addCleanup(os.remove, link)
        run = self.take(cwd=link)
        r = self.run_script("backup", run, "A", os.path.join(link, "src/a.ts"), cwd=link)
        self.assertEqual(r.returncode, 0, r.stderr)
        write(os.path.join(self.repo, "src/a.ts"), "base\nuser edit\nworker\n")
        self.assertEqual(self.run_script("check", run).stdout.strip(), "clean")

    def test_staged_rename_records_the_old_path(self):
        sh(self.repo, "git", "mv", "src/b.ts", "src/c.ts")
        run = self.take()
        write(os.path.join(self.repo, "src/b.ts"), "recreated\n")
        self.assertIn("foreign-changed src/b.ts", self.run_script("check", run).stdout)

if __name__ == "__main__":
    unittest.main()
