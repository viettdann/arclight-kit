import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { runInNewContext } from 'node:vm';

const source = readFileSync(new URL('../plugins/arc-design/skills/ui-check/scripts/ui_check.mjs', import.meta.url), 'utf8');
const start = source.indexOf('  // Targets and names of interactive elements.');
const end = source.indexOf('  // Cursor is inherited', start);
assert.ok(start >= 0 && end > start, 'target audit section must exist');
const targetAudit = source.slice(start, end);

function checkTarget(width, height, mobile) {
  const findings = [];
  const button = {
    tagName: 'BUTTON', textContent: 'Save', labels: [],
    getAttribute: () => null,
    querySelector: () => null,
  };
  runInNewContext(targetAudit, {
    document: { querySelectorAll: () => [button] },
    visible: () => true,
    box: () => ({ width, height }),
    sel: () => 'button',
    mobile,
    add: (check, el, detail) => findings.push({ check, detail }),
  });
  return findings;
}

for (const mobile of [false, true]) {
  test(`compact controls do not require resizing at ${mobile ? 'phone' : 'desktop'} widths`, () => {
    for (const size of [24, 28, 32, 36, 40]) {
      assert.deepEqual(checkTarget(size, size, mobile), [], `${size}px square control`);
      assert.deepEqual(checkTarget(100, size, mobile), [], `${size}px text button`);
    }
  });

  test(`targets below 24px are still reported at ${mobile ? 'phone' : 'desktop'} widths`, () => {
    for (const [width, height] of [[23, 32], [100, 23]]) {
      const findings = checkTarget(width, height, mobile);
      assert.equal(findings.length, 1);
      assert.equal(findings[0].check, 'target');
      assert.match(findings[0].detail, /24px/);
    }
  });
}
