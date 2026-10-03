import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arc-compact.py")


def user(text):
    return {"type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": text}]}}


def assistant(text):
    return {"type": "response_item", "payload": {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": text}]}}


class ArcCompactTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root)

    def run_hook(self, records, raw=None):
        path = os.path.join(self.root, "rollout.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            f.write(raw if raw is not None else "\n".join(json.dumps(r) for r in records) + "\n")
        event = {"hook_event_name": "SessionStart", "source": "compact", "transcript_path": path}
        return subprocess.run([sys.executable, SCRIPT], input=json.dumps(event), capture_output=True, text=True)

    def assert_reinjected(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("still apply", result.stdout)
        self.assertIn("# Arc: daily defaults", result.stdout)
        self.assertIn("**Reach for what exists before writing new.**", result.stdout)
        self.assertNotIn("On invocation:", result.stdout)
        self.assertNotIn("name: arc", result.stdout)

    def assert_silent(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_dollar_mention_in_user_message(self):
        self.assert_reinjected(self.run_hook([user("$arc fix the login bug")]))

    def test_user_message_event(self):
        self.assert_reinjected(self.run_hook([{"type": "event_msg", "payload": {"type": "user_message", "message": "dùng $arc"}}]))

    def test_injected_skill_block(self):
        self.assert_reinjected(self.run_hook([user("<skill>\n<name>arc</name>\n<path>/x/SKILL.md</path>\n</skill>")]))

    def test_plugin_qualified_name(self):
        self.assert_reinjected(self.run_hook([user("use arc-kit:arc")]))

    def test_not_invoked(self):
        self.assert_silent(self.run_hook([user("fix the login bug"), assistant("Done.")]))

    def test_assistant_mention_only(self):
        self.assert_silent(self.run_hook([user("what does it do?"), assistant("Invoke $arc at session start.")]))

    def test_similar_names(self):
        self.assert_silent(self.run_hook([user("$architecture $arc-kit arc-kit:arc-design $$arc")]))

    def test_malformed_lines_are_skipped(self):
        raw = "not json\n" + json.dumps(user("$arc")) + "\n"
        self.assert_reinjected(self.run_hook([], raw=raw))

    def test_missing_transcript(self):
        result = subprocess.run([sys.executable, SCRIPT], input=json.dumps({"transcript_path": os.path.join(self.root, "none")}), capture_output=True, text=True)
        self.assert_silent(result)

    def test_invalid_event(self):
        self.assert_silent(subprocess.run([sys.executable, SCRIPT], input="{", capture_output=True, text=True))


if __name__ == "__main__":
    unittest.main()
