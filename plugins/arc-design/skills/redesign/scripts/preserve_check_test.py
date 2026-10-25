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

    def run_json(self, name, old, new):
        paths = []
        for side, content in (("old", old), ("new", new)):
            os.makedirs(os.path.join(self.root, side), exist_ok=True)
            path = os.path.join(self.root, side, name)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            paths.append(path)
        r = subprocess.run([sys.executable, SCRIPT, *paths, "--json"], capture_output=True, text=True)
        self.assertIn(r.returncode, (0, 1), r.stderr)
        return r.returncode, json.loads(r.stdout)

    def check(self, name, old, new):
        code, out = self.run_json(name, old, new)
        self.assertEqual(code, 1 if out["missing"] else 0)
        return out["missing"]

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

    def test_handler_kinds(self):
        cases = [
            ("a.tsx", '<button onClick={actions.save}>Save</button>\n<Toggle checked={true} onChange={true} />\n', "click=actions.save"),
            ("a.vue", '<button @click.prevent="save">Save</button>\n', "click=save"),
            ("a.svelte", '<button on:click={save}>Save</button>\n', "click=save"),
            ("a.html", '<button onclick="save(event); track()">Save</button>\n', "click=save"),
            ("b.html", '<form onsubmit="return validate(this)"></form>\n', "submit=validate"),
            ("b.vue", '<Comp v-on:click="go" />\n', "click=go"),
            ("c.vue", '<Comp @update:model-value="setValue" />\n', "update:model-value=setValue"),
            ("d.vue", '<button @click="save(item)">Save</button>\n', "click=save"),
            ("b.svelte", '<form on:submit|preventDefault={save}></form>\n', "submit=save"),
            ("c.svelte", '<button onclick={save}>Save</button>\n', "click=save"),
        ]
        for name, old, value in cases:
            with self.subTest(name=name):
                missing = self.check(name, '<a href="/x">x</a>\n' + old, '<a href="/x">x</a>\n<button>Save</button>\n')
                self.assertEqual(missing, {"handler": [value]})

    def test_svelte_transition_is_not_a_handler(self):
        old = '<a href="/x">x</a>\n<div transition:slide={opts}>x</div>\n'
        self.assertEqual(self.check("a.svelte", old, '<a href="/x">x</a>\n<div>x</div>\n'), {})

    def test_no_wiring_in_original_exits_two(self):
        paths = []
        for side, content in (("old", "<h1>Plans</h1>\n<p>Save 50%</p>\n"), ("new", "<h1>Pricing</h1>\n")):
            os.makedirs(os.path.join(self.root, side))
            paths.append(os.path.join(self.root, side, "a.html"))
            with open(paths[-1], "w", encoding="utf-8") as f:
                f.write(content)
        self.assertEqual(subprocess.run([sys.executable, SCRIPT, *paths], capture_output=True).returncode, 2)

    def test_text_output_lists_changed_content(self):
        paths = []
        for side, content in (("old", '<a href="/x">x</a>\n<h2>Plans</h2>\n'), ("new", '<a href="/x">x</a>\n<h2>Pricing</h2>\n')):
            os.makedirs(os.path.join(self.root, side))
            paths.append(os.path.join(self.root, side, "a.html"))
            with open(paths[-1], "w", encoding="utf-8") as f:
                f.write(content)
        r = subprocess.run([sys.executable, SCRIPT, *paths], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        self.assertIn("Changed content (check each is intended):", r.stdout)
        self.assertIn("Plans", r.stdout)
        self.assertNotIn("All ", r.stdout)

    def test_inline_handler_ignored(self):
        old = '<a href="/x">x</a>\n<button onClick={() => x()}>Go</button>\n'
        new = '<a href="/x">x</a>\n<button>Go</button>\n'
        self.assertEqual(self.check("a.tsx", old, new), {})

    def test_script_src(self):
        old = '<script src="/js/app.js"></script>\n<script src={cdn + "/x.js"}></script>\n'
        new = '<script src="/js/other.js"></script>\n'
        self.assertEqual(self.check("a.html", old, new), {"script": ["/js/app.js"]})

    def test_selector_strings(self):
        old = 'document.querySelector(".cart-count"); el.closest("[data-row]"); document.getElementById(`tab-${i}`);\n'
        new = 'document.querySelector(".cart-total");\n'
        self.assertEqual(self.check("a.js", old, new), {"selector": [".cart-count", "[data-row]"]})

    def test_warn_only_exits_zero(self):
        old = '<a href="/pricing">Pricing</a>\n<h2>Plans for <em>every</em>\n team</h2>\n<p>Save 20% today.</p>\n'
        new = '<a href="/pricing">Pricing</a>\n<h2>Pick a plan</h2>\n<p>Save 20% today.</p>\n'
        code, out = self.run_json("a.html", old, new)
        self.assertEqual(code, 0)
        self.assertEqual(out["missing"], {})
        self.assertEqual(out["warn"], {"heading": ["Plans for every team"]})

    def test_kept_counts(self):
        old = '<a href="/a">A</a><a href="/b">B</a><a href="/c">C</a>\n<img src="/hero.png">\n<p>From $29.</p>\n'
        new = '<a href="/a">A</a>\n<img src="/hero.png">\n<p>From $19</p>\n'
        _, out = self.run_json("a.html", old, new)
        self.assertEqual(out["kept"], {"href": [1, 3], "image": [1, 1], "figure": [0, 1]})
        self.assertEqual(out["warn"], {"figure": ["$29"]})


if __name__ == "__main__":
    unittest.main()
