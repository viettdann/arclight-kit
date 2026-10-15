import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { test } from 'node:test';
import { runInNewContext } from 'node:vm';

const checker = new URL('../plugins/arc-design/skills/design/scripts/contrast.mjs', import.meta.url);
const source = readFileSync(new URL('../plugins/arc-design/skills/ui-check/scripts/ui_check.mjs', import.meta.url), 'utf8');

function check(...pairs) {
  return spawnSync(process.execPath, [checker.pathname, ...pairs], { encoding: 'utf8' });
}

test('APCA warns on weak mid-tone text without changing WCAG exit status', () => {
  const result = check('#141413|#E35336|text', '#ffffff|#CC4329|text');
  assert.equal(result.status, 0);
  assert.match(result.stdout, /warn\s+4\.88:1\s+Lc\s+39/);
  assert.match(result.stdout, /pass\s+4\.77:1\s+Lc\s+-77/);
});

test('contrast failures and invalid inputs keep distinct exit statuses', () => {
  assert.equal(check('#ffffff|#ffffff|text').status, 1);
  assert.equal(check('invalid|#ffffff|text').status, 2);
});

test('media contrast uses CSS fill instead of antialiased screenshot pixels', async () => {
  const start = source.indexOf('const mediaContrast = async');
  const end = source.indexOf('\nconst url =', start);
  const mathStart = source.indexOf('const lum =');
  const mathEnd = source.indexOf('// Chrome', mathStart);
  assert.ok(start >= 0 && end > start && mathStart >= 0 && mathEnd > mathStart);
  const background = [227, 83, 54];
  const shown = { px: Uint8Array.from(Array(16).fill([150, 40, 20]).flat()), ch: 3 };
  const bare = { px: Uint8Array.from(Array(16).fill(background).flat()), ch: 3 };
  let shots = 0;
  const run = runInNewContext(`${source.slice(mathStart, mathEnd)}\n${source.slice(start, end)}\nmediaContrast`, {
    evaluate: async (expression) => expression.includes('getBoundingClientRect')
      ? { fill: [20, 20, 19, 1], selector: 'p', text: 'Example', min: 4.5, lcMin: 60, clip: { width: 20, height: 20 } }
      : undefined,
    send: async () => ({ data: shots++ === 0 ? shown : bare }),
    decodePng: (value) => value,
  });
  const result = await run(0);
  assert.equal(shots, 2);
  assert.equal(result.pixels, 16);
  assert.equal(result.ratio, 4.87);
  assert.equal(result.lc, 39);
});
