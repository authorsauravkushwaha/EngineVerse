/* Optional real-browser smoke test; no application dependency.
 * npm install --prefix .toolchain/browser playwright-core@1.56.1 @sparticuz/chromium@141.0.0
 * node scripts/check_academy_browser.js [http://127.0.0.1:8000]
 * The target must be a disposable, optionally browsable catalogue with judging disabled.
 */
const assert = require('node:assert/strict');
const path = require('node:path');
const { chromium } = require('../.toolchain/browser/node_modules/playwright-core');
const binary = require('../.toolchain/browser/node_modules/@sparticuz/chromium');

(async () => {
  const browser = await chromium.launch({args: binary.args, executablePath: await binary.executablePath(), headless: true});
  const context = await browser.newContext({viewport: {width: 1440, height: 1100}});
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const base = process.argv[2] || 'http://127.0.0.1:8000';
  const lesson = '/programming/python/lessons/python-loops-from-scratch';
  const uploads = [];
  page.on('request', request => { if (request.method() !== 'GET') uploads.push(request.url()); });
  await page.goto(base + lesson);
  await page.locator('#academy-attempt').waitFor();
  assert.equal(await page.locator('#academy-solution').isVisible(), false);
  await page.locator('[data-trace-next]').click();
  assert.match(await page.locator('[data-trace-status]').innerText(), /Step 1 of 4/);
  await page.locator('[data-trace-next]').click();
  assert.equal(await page.locator('tr[aria-current="step"]').count(), 1);
  await page.locator('#academy-code').fill('total = 0\n# my local draft');
  await page.locator('#academy-code').focus();
  // Tab follows the native focus order to the attempt button, Enter activates it.
  await page.keyboard.press('Tab');
  assert.match(await page.locator(':focus').innerText(), /Record attempt/);
  await page.keyboard.press('Enter');
  assert.equal(await page.locator('#academy-solution').isVisible(), true);
  await page.keyboard.press('Enter'); // focused summary opens the reference
  assert.equal(await page.locator('#academy-solution').getAttribute('open'), '');
  assert.match(await page.locator('#academy-attempt-status').innerText(), /Nothing was run/);
  await page.getByRole('button', {name: 'Reset and retry'}).click();
  assert.equal(await page.locator('#academy-code').inputValue(), '');
  assert.equal(await page.locator('#academy-solution').isVisible(), false);
  assert.equal(uploads.length, 0, 'local practice must not upload submissions');
  // Inspect widths at desktop, tablet and phone sizes.
  for (const width of [1440, 768, 390]) {
    await page.setViewportSize({width, height: 1000});
    await page.goto(base + lesson);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
    assert.equal(overflow, false, `horizontal overflow at ${width}px`);
    assert.equal(await page.getByRole('heading', {name: 'A · Learning objectives'}).isVisible(), true);
    if (process.env.ACADEMY_SCREENSHOTS && width !== 768) {
      await page.screenshot({path: path.join(process.env.ACADEMY_SCREENSHOTS, `academy-${width}.png`)});
    }
  }
  await page.goto(base + '/programming/python');
  await page.locator('#module-filter').fill('growth rates');
  assert.equal(await page.locator('[data-module-card]:visible').count(), 1);
  await page.locator('#module-filter').fill('no-such-module-12345');
  assert.equal(await page.locator('[data-module-card]:visible').count(), 0);
  assert.match(await page.locator('#module-filter-status').innerText(), /0 matching/);
  await page.locator('#module-filter').fill('');
  assert.equal(await page.locator('[data-module-card]:visible').count(), 35);
  const noJs = await browser.newContext({javaScriptEnabled: false, viewport: {width: 390, height: 844}});
  const staticPage = await noJs.newPage();
  await staticPage.goto(base + lesson);
  assert.equal(await staticPage.locator('#academy-solution').isVisible(), true);
  assert.equal(await staticPage.locator('[data-trace] tbody tr').count(), 4);
  await staticPage.locator('#academy-solution summary').click();
  assert.equal(await staticPage.locator('#academy-solution pre').first().isVisible(), true);
  assert.deepEqual(errors, []);
  console.log('PASS: desktop/tablet/mobile widths, keyboard attempt/retry, trace, filtering, no-JS fallback; no uploads or browser errors.');
  await browser.close();
})().catch(error => { console.error(error); process.exit(1); });
