import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preserve_check.py")


class PreserveCheckTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root)

    def check(self, name, old, new):
        paths = []
        for side, content in (("old", old), ("new", new)):
            os.makedirs(os.path.join(self.root, side), exist_ok=True)
            path = os.path.join(self.root, side, name)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            paths.append(path)
        r = subprocess.run([sys.executable, SCRIPT, *paths, "--json"], capture_output=True, text=True)
        self.assertIn(r.returncode, (0, 1), r.stderr)
        missing = json.loads(r.stdout)["missing"]
        self.assertEqual(r.returncode, 1 if missing else 0)
        return missing

    def test_removed_canonical_link_is_reported_as_canonical_not_href(self):
        old = '<head><title>P</title><link rel="canonical" href="https://ex.com/p"></head>\n'
        new = "<head><title>P</title></head>\n"
        missing = self.check("a.html", old, new)
        self.assertEqual(missing.get("canonical"), ["https://ex.com/p"])
        self.assertNotIn("href", missing)

    def test_changed_og_image_reports_old_value(self):
        old = '<head><meta property="og:image" content="https://ex.com/a.png"></head>\n'
        new = '<head><meta property="og:image" content="https://ex.com/b.png"></head>\n'
        self.assertEqual(self.check("a.html", old, new).get("share tags"), ["og:image=https://ex.com/a.png"])

    def test_removed_metadata_api_canonical(self):
        old = "export const metadata = { title: 'Pricing', alternates: { canonical: '/pricing' } };\n"
        new = "export const metadata = { title: 'Pricing' };\n"
        self.assertEqual(self.check("page.tsx", old, new).get("canonical"), ["/pricing"])

    def test_removed_use_head_canonical_link(self):
        old = "useHead({ title: 'Pricing', link: [{ rel: 'canonical', href: 'https://ex.com/pricing' }] })\n"
        new = "useHead({ title: 'Pricing' })\n"
        self.assertEqual(self.check("p.vue", old, new).get("canonical"), ["https://ex.com/pricing"])

    def test_computed_share_tag_content_is_not_captured(self):
        old = '<meta property="og:title" content="Post" />\n<meta property="og:image" content={post.image} />\n'
        new = '<meta property="og:title" content="Post" />\n<meta property="og:image" content={post.cover} />\n'
        self.assertEqual(self.check("a.tsx", old, new), {})


if __name__ == "__main__":
    unittest.main()
