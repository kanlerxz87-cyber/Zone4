// Local rendered-layout fixtures only. Never activate a sponsored link or telemetry.
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const http = require('node:http');
const path = require('node:path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '../..');
const DOCS = path.join(ROOT, 'docs');
const RESULTS = path.join(ROOT, 'build/browser-qa/results');
const PREFIX = '/Zone4/docs/';
const DISCLOSURE = 'As an Amazon Associate I earn from qualifying purchases.';
const VIEWPORTS = [
  { width: 320, height: 568 },
  { width: 375, height: 667 },
  { width: 390, height: 844 },
  { width: 768, height: 1024 },
  { width: 1440, height: 1000 },
];
const TYPES = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8', '.xml': 'application/xml; charset=utf-8',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.svg': 'image/svg+xml',
};

async function pages(directory = DOCS) {
  const entries = await fs.readdir(directory, { withFileTypes: true });
  return (await Promise.all(entries.map(async entry => {
    const file = path.join(directory, entry.name);
    if (entry.isDirectory()) return pages(file);
    return entry.isFile() && file.endsWith('.html') ? [path.relative(DOCS, file).split(path.sep).join('/')] : [];
  }))).flat().sort();
}

function staticServer() {
  return http.createServer(async (request, response) => {
    try {
      const url = new URL(request.url, 'http://fixture.invalid');
      const file = path.resolve(DOCS, decodeURIComponent(url.pathname.slice(PREFIX.length)));
      if (!['GET', 'HEAD'].includes(request.method) || !url.pathname.startsWith(PREFIX)
          || !file.startsWith(DOCS + path.sep)) {
        response.writeHead(404).end();
        return;
      }
      const body = await fs.readFile(file);
      response.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
      response.end(request.method === 'HEAD' ? undefined : body);
    } catch {
      response.writeHead(404).end();
    }
  });
}

async function observations(page) {
  return page.evaluate(() => {
    const box = element => {
      const r = element.getBoundingClientRect();
      const style = getComputedStyle(element);
      return { top: r.top, right: r.right, bottom: r.bottom, left: r.left, width: r.width, height: r.height,
        displayed: style.display !== 'none' && style.visibility !== 'hidden' && Number(style.opacity) !== 0 };
    };
    const disclosure = document.querySelector('.content > .disclosure');
    return {
      viewport: { width: innerWidth, height: innerHeight },
      documentWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
      title: document.querySelector('h1')?.textContent.trim(),
      headlineCount: document.querySelectorAll('h1').length,
      masthead: box(document.querySelector('.masthead')),
      disclosure: { ...box(disclosure), text: disclosure.textContent.trim() },
      endpoint: document.querySelector('meta[name="zone4-measure-endpoint"]')?.content,
      confirmations: [...document.querySelectorAll('#launch-checklist tbody tr')].map(row => row.cells[4].textContent.trim()),
    };
  });
}

async function checkKeyboardMenus(page) {
  const summaries = page.locator('.topnav details > summary');
  assert.ok(await summaries.count() > 0, 'Native navigation directory must remain reachable without JavaScript');
  for (const summary of await summaries.all()) {
    await summary.focus();
    await summary.press('Enter');
    assert.equal(await summary.evaluate(el => el.parentElement.open), true, 'Enter must open the native menu');
    const panel = summary.locator('..').locator('.nav-panel');
    const bounds = await panel.boundingBox();
    const viewport = page.viewportSize();
    assert.ok(bounds && bounds.x >= -1 && bounds.x + bounds.width <= viewport.width + 1, 'Open menu overflows horizontally');
    assert.ok(bounds.y >= 0 && bounds.y + bounds.height <= viewport.height + 1, 'Open menu is outside the viewport');
    await summary.press('Tab');
    assert.equal(await panel.locator('a').first().evaluate(el => el === document.activeElement), true, 'Tab must reach the first menu destination');
    await panel.locator('a').last().focus();
    assert.equal(await panel.locator('a').last().evaluate(el => el === document.activeElement), true, 'Last menu destination must remain focusable');
    await summary.focus();
    await summary.press('Space');
    assert.equal(await summary.evaluate(el => el.parentElement.open), false, 'Space must close the menu');
  }
  const coverage = await page.evaluate(() => {
    const nav = new Set([...document.querySelectorAll('.topnav a')].map(a => a.href));
    return [...document.querySelectorAll('.footer-directory a')].filter(a => !nav.has(a.href)).map(a => a.getAttribute('href'));
  });
  assert.deepEqual(coverage, [], 'Every footer directory destination must also be in the one navigation group');
}

(async () => {
  await fs.mkdir(RESULTS, { recursive: true });
  const server = staticServer();
  let browser, activePage;
  const report = { kind: 'isolated local layout fixtures, not visitor or campaign data', pages: [], keyboard: [], status: 'running' };
  try {
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    const origin = `http://127.0.0.1:${server.address().port}`;
    const executablePath = process.env.ZONE4_CHROMIUM_EXECUTABLE;
    browser = await chromium.launch({ headless: true, ...(executablePath ? {
      executablePath, args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
    } : {}) });
    const published = await pages();
    assert.ok(published.length > 0, 'Build docs/ before checking it');
    const settings = JSON.parse(await fs.readFile(path.join(ROOT, 'data/measurement.json'), 'utf8'));
    assert.equal(settings.enabled, false, 'These fixtures are for an explicitly disabled publication, never production telemetry');
    for (const viewport of VIEWPORTS) {
      const context = await browser.newContext({ viewport });
      activePage = await context.newPage();
      const errors = [];
      activePage.on('pageerror', error => errors.push(error.message));
      activePage.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
      activePage.on('response', response => { if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
      await context.route('**/*', async route => {
        if (new URL(route.request().url()).origin === origin) {
          assert.notEqual(new URL(route.request().url()).pathname, '/event', 'No measurement request is allowed');
          await route.continue();
        } else {
          errors.push(`External request blocked: ${route.request().url()}`);
          await route.abort();
        }
      });
      for (const file of published) {
        const response = await activePage.goto(origin + PREFIX + file, { waitUntil: 'load' });
        assert.equal(response.status(), 200, file);
        const stats = await observations(activePage);
        const label = `${viewport.width}x${viewport.height}/${file}`;
        report.pages.push({ file, ...stats });
        assert.equal(stats.headlineCount, 1, `${label}: expected one main headline`);
        assert.equal(stats.endpoint, '', `${label}: collection must remain disabled`);
        assert.ok(stats.documentWidth <= stats.clientWidth + 1, `${label}: document overflows (${stats.documentWidth} > ${stats.clientWidth})`);
        assert.ok(stats.disclosure.text.includes(DISCLOSURE), `${label}: Associates disclosure is missing`);
        assert.ok(stats.disclosure.displayed && stats.disclosure.height > 0 && stats.disclosure.top >= stats.masthead.bottom - 1,
          `${label}: disclosure must be visible below the masthead`);
        assert.ok(stats.disclosure.bottom <= viewport.height, `${label}: disclosure is below the first screen`);
        if (file === 'measurement.html') assert.deepEqual(stats.confirmations, ['', '', '', '', ''], 'Never fabricate launch confirmations');
        assert.deepEqual(errors, [], `${label}: browser/runtime/resource error`);
      }
      await context.close();
      // Native menus must work without the app or measurement JavaScript.
      if ([320, 390, 1440].includes(viewport.width)) {
        const context = await browser.newContext({ viewport, javaScriptEnabled: false });
        await context.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
        activePage = await context.newPage();
        for (const file of ['index.html', 'measurement.html', 'guides/index.html']) {
          await activePage.goto(origin + PREFIX + file, { waitUntil: 'load' });
          await checkKeyboardMenus(activePage);
          report.keyboard.push({ viewport, file, javascript: false, passed: true });
        }
        await context.close();
      }
    }
    report.status = 'passed';
    console.log(`PASS: ${published.length} published pages × ${VIEWPORTS.length} viewports; ${report.keyboard.length} no-script keyboard-menu checks; no external navigation or collection.`);
  } catch (error) {
    report.status = 'failed';
    report.error = error.stack || String(error);
    if (activePage && !activePage.isClosed()) await activePage.screenshot({ path: path.join(RESULTS, 'failure.png') }).catch(() => {});
    console.error(error);
    process.exitCode = 1;
  } finally {
    await fs.writeFile(path.join(RESULTS, 'report.json'), JSON.stringify(report, null, 2) + '\n');
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})();
