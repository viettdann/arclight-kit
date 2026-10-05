import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scan_tells.py")


class ScanTellsTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root)

    def tells(self, name, content):
        path = os.path.join(self.root, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        r = subprocess.run([sys.executable, SCRIPT, path, "--json"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return [h["tell"] for hs in json.loads(r.stdout).values() for h in hs]

    def assertTell(self, name, content, prefix):
        self.assertTrue(any(prefix in t for t in self.tells(name, content)), f"expected '{prefix}' in {content!r}")

    def assertNoTell(self, name, content, prefix):
        self.assertEqual([t for t in self.tells(name, content) if prefix in t], [], f"unexpected '{prefix}' in {content!r}")

    def test_side_border_tailwind(self):
        self.assertTell("a.tsx", '<div className="border-l-4 border-blue-500 p-4">x</div>\n', "colored side border")
        self.assertNoTell("a.tsx", '<div className="border-l-4 border-zinc-200 p-4">x</div>\n', "colored side border")
        self.assertNoTell("a.tsx", '<div className="border-l-2 border-accent/20 pl-4">x</div>\n', "colored side border")

    def test_side_border_current_item_is_kept(self):
        self.assertNoTell("a.tsx", '<a aria-current="page" className="border-l-2 border-blue-500">Home</a>\n', "colored side border")

    def test_side_border_css(self):
        self.assertTell("a.css", ".card {\n  border-left: 4px solid #2563eb;\n}\n", "colored side border")
        self.assertNoTell("a.css", ".card {\n  border-left: 4px solid #e5e7eb;\n}\n", "colored side border")
        self.assertNoTell("a.css", "blockquote {\n  border-left: 4px solid #2563eb;\n}\n", "colored side border")

    def test_overshoot_easing(self):
        self.assertTell("a.css", ".a { transition-timing-function: cubic-bezier(0.34, 1.56, 0.64, 1); }\n", "overshoot easing")
        self.assertTell("a.tsx", '<div className="ease-[cubic-bezier(0.6,-0.28,0.74,0.05)]" />\n', "overshoot easing")
        self.assertNoTell("a.css", ":root { --ease-enter: cubic-bezier(0.16, 1, 0.3, 1); }\n", "overshoot easing")

    def test_transition_all(self):
        self.assertTell("a.tsx", '<button className="transition-all duration-200">x</button>\n', "transition: all")
        self.assertTell("a.css", ".a { transition: all 200ms; }\n", "transition: all")
        self.assertNoTell("a.css", ".a { transition: opacity 200ms, transform 200ms; }\n", "transition: all")

    def test_layout_transition(self):
        self.assertTell("a.css", ".a { transition: height 300ms ease; }\n", "layout property")
        self.assertTell("a.tsx", '<div className="transition-[width] duration-200" />\n', "layout property")
        self.assertNoTell("a.css", ".a { transition: background-color 150ms, border-color 150ms; }\n", "layout property")

    def test_tight_tracking(self):
        self.assertTell("a.tsx", '<h1 className="tracking-[-0.05em]">x</h1>\n', "tracking tighter")
        self.assertTell("a.css", "h1 { letter-spacing: -0.06em; }\n", "tracking tighter")
        self.assertTell("a.tsx", '<h1 className="tracking-tighter">x</h1>\n', "tracking tighter")
        self.assertNoTell("a.css", "h1 { letter-spacing: -0.04em; }\n", "tracking tighter")
        self.assertNoTell("a.tsx", '<h1 className="tracking-[-0.02em]">x</h1>\n', "tracking tighter")

    def test_hairline_with_large_shadow(self):
        self.assertTell("a.tsx", '<div className="rounded-xl border shadow-2xl">x</div>\n', "hairline border plus")
        self.assertTell("a.css", ".card {\n  border: 1px solid #e5e5e5;\n  box-shadow: 0 20px 40px rgba(0,0,0,.1);\n}\n", "hairline border plus")
        self.assertNoTell("a.tsx", '<div className="rounded-xl border shadow-sm">x</div>\n', "hairline border plus")
        self.assertNoTell("a.tsx", '<div role="dialog" className="fixed inset-0 rounded-xl border shadow-2xl">x</div>\n', "hairline border plus")
        self.assertNoTell("a.css", ".card {\n  border: none;\n  box-shadow: 0 20px 40px rgba(0,0,0,.1);\n}\n", "hairline border plus")

    def test_justify(self):
        self.assertTell("a.tsx", '<p className="text-justify">x</p>\n', "justified text")
        self.assertTell("a.css", "p { text-align: justify; }\n", "justified text")
        self.assertNoTell("a.tsx", '<div className="flex justify-between">x</div>\n', "justified text")

    def test_outline_without_focus_visible(self):
        self.assertTell("a.tsx", '<input className="outline-none border" />\n', "outline removed")
        self.assertTell("a.css", "button { outline: none; }\n", "outline removed")
        self.assertNoTell("a.tsx", '<input className="outline-none focus-visible:ring-2" />\n', "outline removed")
        self.assertNoTell("a.tsx", '<div className="px-2 outline-none data-[highlighted]:bg-zinc-100">x</div>\n', "outline removed")
        self.assertNoTell("a.tsx", '<div tabIndex={-1} className="fixed inset-0 outline-none">x</div>\n', "outline removed")
        self.assertNoTell("a.css", "button { outline: none; }\nbutton:focus-visible { outline: 2px solid; }\n", "outline removed")
        self.assertNoTell("a.css", "button { outline: none; }\nbutton:focus { outline: 2px solid; }\n", "outline removed")
        self.assertTell("a.css", ".btn:focus { outline: none; }\n", "outline removed")
        self.assertTell("a.css", ".btn:focus { outline: 0; }\n", "outline removed")

    def test_reveal_without_guard(self):
        self.assertTell("a.css", ".reveal {\n  opacity: 0;\n  transform: translateY(16px);\n}\n", "hidden reveal")
        self.assertTell("a.tsx", '<section className="reveal opacity-0 translate-y-4">x</section>\n', "hidden reveal")
        self.assertNoTell("a.css", ".js .reveal {\n  opacity: 0;\n}\n", "hidden reveal")
        self.assertNoTell("a.css", ".tooltip {\n  opacity: 0;\n}\n", "hidden reveal")
        self.assertNoTell("a.css", "@keyframes reveal { from { opacity: 0; } to { opacity: 1; } }\n", "hidden reveal")

    def test_stock_phrases(self):
        self.assertTell("a.html", "<h1>The future of invoicing</h1>\n", "stock headline phrase")
        self.assertTell("a.html", "<h2>Meet your new assistant</h2>\n", "stock headline phrase")
        self.assertTell("a.html", "<p>Built for finance teams</p>\n", "stock headline phrase")
        self.assertNoTell("a.html", "<h1>Close the books in two days</h1>\n", "stock headline phrase")
        self.assertNoTell("a.ts", "// the cache is built for each request\n", "stock headline phrase")

    def test_learn_more(self):
        self.assertTell("a.html", '<a href="/x">Learn more &rarr;</a>\n', "'Learn more'")
        self.assertNoTell("a.html", '<a href="/x">Learn more about pricing</a>\n', "'Learn more'")

    def test_centered_aggregate(self):
        items = "".join(f"<p>line {k}</p>" for k in range(8))
        self.assertTell("a.html", f'<section class="text-center"><h2>T</h2>{items}</section>\n', "text blocks centered")
        self.assertNoTell("a.html", f'<section class="text-center"><h2>T</h2></section><div>{items}</div>\n', "text blocks centered")
        self.assertNoTell("a.html", f'<section class="text-center"><h2>T</h2><div class="text-left">{items}</div></section>\n', "text blocks centered")

    def test_centered_stray_angle_brackets_stay_linear(self):
        content = "const x = a <b ? c : d;\nconst y = a <b ? \"c : d;\nconst z = a <b ? 'c : d;\n" * 1334
        start = time.monotonic()
        self.tells("a.tsx", content)
        self.assertLess(time.monotonic() - start, 2)

    def test_centered_multiline_tag(self):
        items = "".join(f"<p>line {k}</p>\n" for k in range(8))
        self.assertTell("a.tsx", f'<section\n  className="text-center"\n  title="a > b"\n>\n<h2>T</h2>\n{items}</section>\n', "text blocks centered")


if __name__ == "__main__":
    unittest.main()
