import test from 'node:test';
import assert from 'node:assert/strict';
test('phone preview blocks draft diagnostics while keeping normal API forwarding', async () => {
  process.env.MATCHOS_PHONE_ADDRESS = '192.168.1.20';
  try {
    const { default: config } = await import('../vite.config.js?phone-test');
    const rule = config.preview.proxy['/api'];
    assert.equal(rule.target, 'http://127.0.0.1:8000');
    assert.equal(rule.changeOrigin, true);
    const response = {
      end(body) {
        this.body = body;
      },
    };
    assert.equal(rule.bypass({ url: '/api/development/matches/x/catch-up' }, response), false);
    assert.equal(response.statusCode, 404);
    assert.equal(rule.bypass({ url: '/api/%64evelopment/matches/x/catch-up' }, response), false);
    assert.equal(response.statusCode, 404);
    assert.equal(rule.bypass({ url: '/api/matchdays/start' }, {}), undefined);
  } finally {
    delete process.env.MATCHOS_PHONE_ADDRESS;
  }
});
