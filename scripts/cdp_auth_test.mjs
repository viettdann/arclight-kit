import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { test } from 'node:test';

const moduleUrl = new URL('../plugins/arc-design/skills/design/scripts/cdp.mjs', import.meta.url).href;
const secret = 'FAKE_SECRET_FOR_REGRESSION';

for (const [name, cookies, headers, rejection] of [
  ['invalid cookie', [secret], [], 'invalid'],
  ['rejected cookie', [`session=${secret}`], [], 'rejected'],
  ['cookie protocol error', [`session=${secret}`], [], 'throws'],
  ['invalid header', [], [`Authorization: ${secret}\ninvalid`], 'invalid'],
]) {
  test(`${name} does not expose credentials`, () => {
    const source = `
      import { applyAuth } from ${JSON.stringify(moduleUrl)};
      await applyAuth({
        send: async () => {
          if (${JSON.stringify(rejection)} === 'throws') throw new Error(${JSON.stringify(secret)});
          return { success: false };
        },
        on: () => {},
      }, 'https://example.test', ${JSON.stringify(cookies)}, ${JSON.stringify(headers)});
    `;
    const result = spawnSync(process.execPath, ['--input-type=module', '-e', source], { encoding: 'utf8' });
    assert.equal(result.status, 2);
    assert.match(result.stderr, /--cookie|--header/);
    assert.ok(!`${result.stdout}${result.stderr}`.includes(secret), result.stderr);
  });
}

test('header protocol errors hide credentials and continue the request', () => {
  const source = `
    import assert from 'node:assert/strict';
    import { applyAuth } from ${JSON.stringify(moduleUrl)};
    let handler;
    const calls = [];
    await applyAuth({
      send: async (method, params) => {
        calls.push({ method, params });
        if (method === 'Fetch.continueRequest' && params.headers) throw new Error(${JSON.stringify(secret)});
        return {};
      },
      on: (_, callback) => { handler = callback; },
    }, 'https://example.test', [], ['Authorization: Bearer ' + ${JSON.stringify(secret)}]);
    handler({ requestId: '1', request: { headers: {}, url: 'https://example.test/?token=' + ${JSON.stringify(secret)} } });
    await new Promise((resolve) => setImmediate(resolve));
    assert.equal(calls[1].params.headers[0].value, 'Bearer ' + ${JSON.stringify(secret)});
    assert.deepEqual(calls[2], { method: 'Fetch.continueRequest', params: { requestId: '1' } });
  `;
  const result = spawnSync(process.execPath, ['--input-type=module', '-e', source], { encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stderr, /--header rejected by Chrome/);
  assert.ok(!`${result.stdout}${result.stderr}`.includes(secret), result.stderr);
});
