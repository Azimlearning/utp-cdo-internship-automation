// Shared helpers for the Playwright sandbox scripts. tools/sandbox/pw.py pastes this file, the call's parameters (P) and
// one entry point into tmp/pw/<cmd>.js, which is then run with browser_run_code_unsafe(filename=...).
//
// Auth: the Power Automate page already calls api.flow.microsoft.com with the signed-in user's bearer token. We read that
// header off one of the page's own requests and keep it in memory on the page object (page.__flowAuth). It is never
// returned, printed or written to disk, and only ever sent back to api.flow.microsoft.com.
// SharePoint REST calls go through page.request, which carries the browser context's cookies.

const PA = 'https://make.powerautomate.com';

async function ensureAuth(page, P) {
  const A = page.__flowAuth;
  if (A && Date.now() - A.at < 40 * 60 * 1000) return A;
  let tok = null, base = null;
  const h = req => {
    const m = req.url().match(/^(https:\/\/[^/]*api\.flow\.microsoft\.com)/);
    const a = req.headers()['authorization'];
    if (m && a && !tok) { tok = a; base = m[1]; }
  };
  page.on('request', h);
  await page.goto(`${PA}/environments/${P.env}/flows`);
  for (let i = 0; i < 30 && !tok; i++) await page.waitForTimeout(1000);
  page.off('request', h);
  if (!tok) throw new Error('could not capture the Power Automate token: is the browser signed in?');
  page.__flowAuth = { tok, base, at: Date.now() };
  return page.__flowAuth;
}

async function api(page, P, method, path, body) {
  let A = await ensureAuth(page, P);
  const url = () => `${A.base}/providers/Microsoft.ProcessSimple/environments/${P.env}${path}${path.includes('?') ? '&' : '?'}api-version=2016-11-01`;
  let r = await page.request.fetch(url(), { method, headers: { Authorization: A.tok, 'Content-Type': 'application/json' }, data: body });
  if (r.status() === 401) { // the page's token can be near expiry when captured: take a fresh one and retry once
    page.__flowAuth = null;
    A = await ensureAuth(page, P);
    r = await page.request.fetch(url(), { method, headers: { Authorization: A.tok, 'Content-Type': 'application/json' }, data: body });
  }
  const txt = await r.text();
  let j = null; try { j = JSON.parse(txt); } catch (e) {}
  if (r.status() >= 400) throw new Error(`${method} ${path} -> ${r.status()} ${(j && j.error && j.error.message) || txt.slice(0, 200)}`);
  return j;
}

async function listFlows(page, P) {
  const out = [];
  let j = await api(page, P, 'GET', '/flows?$top=50');
  for (let i = 0; i < 20; i++) {
    for (const f of j.value || []) out.push({ id: f.name, name: f.properties.displayName, state: f.properties.state, created: f.properties.createdTime });
    const A = page.__flowAuth; // api() may have refreshed the token: always use the current one
    if (!j.nextLink || !j.nextLink.startsWith(A.base + '/')) break;
    const r = await page.request.get(j.nextLink, { headers: { Authorization: A.tok } });
    const t = await r.text();
    if (r.status() >= 400 || !t) throw new Error(`listing flows (page ${i + 2}) -> ${r.status()} ${t.slice(0, 200)}`);
    j = JSON.parse(t);
  }
  return out;
}

// Never touch anything that isn't a sandbox copy.
function assertSandbox(f) {
  if (!f || !/^\[SANDBOX-/.test(f.name)) throw new Error(`refusing to act on a non-sandbox flow: ${f && f.name}`);
}

function newest(flows, name) {
  const m = flows.filter(f => f.name === name).sort((a, b) => b.created.localeCompare(a.created));
  return m[0];
}

async function setState(page, P, f, on) {
  assertSandbox(f);
  await api(page, P, 'POST', `/flows/${f.id}/${on ? 'start' : 'stop'}`);
  const s = (await api(page, P, 'GET', `/flows/${f.id}`)).properties.state;
  if (s !== (on ? 'Started' : 'Stopped')) throw new Error(`${f.name}: state is ${s} after ${on ? 'start' : 'stop'}`);
  return s;
}

// Every sandbox copy of the same flow (other package, older imports) must be off before one is turned on,
// otherwise one trigger item fires several copies.
async function stopTwins(page, P, flows, target) {
  const suffix = target.name.replace(/^\[SANDBOX-[A-Z]+\] /, '');
  const stopped = [];
  for (const f of flows) {
    if (f.id !== target.id && f.state === 'Started' && /^\[SANDBOX-/.test(f.name) && f.name.endsWith('] ' + suffix)) {
      await setState(page, P, f, false); stopped.push(f.name);
    }
  }
  return stopped;
}

// ---- SharePoint (sandbox site only) ----
async function sp(page, P, method, path, body, extra) {
  if (!P.site.includes('-my.sharepoint.com/personal/')) throw new Error('refusing SharePoint call outside the sandbox OneDrive site');
  const H = { Accept: 'application/json;odata=nometadata', 'Content-Type': 'application/json;odata=nometadata', ...(extra || {}) };
  if (method !== 'GET') {
    if (!page.__spDigest || Date.now() - page.__spDigest.at > 20 * 60 * 1000) {
      const d = await page.request.post(`${P.site}/_api/contextinfo`, { headers: H });
      const dt = await d.text();
      if (d.status() >= 400 || !dt) throw new Error(`SharePoint contextinfo -> ${d.status()} (signed out of SharePoint?)`);
      page.__spDigest = { v: JSON.parse(dt).FormDigestValue, at: Date.now() };
    }
    H['X-RequestDigest'] = page.__spDigest.v;
  }
  const go = () => page.request.fetch(`${P.site}/_api/web/${path}`, { method: method === 'DELETE' ? 'POST' : method, headers: method === 'DELETE' ? { ...H, 'IF-MATCH': '*', 'X-HTTP-Method': 'DELETE' } : H, data: body ? JSON.stringify(body) : undefined });
  let r = await go();
  if (r.status() === 401 && !extra) { // SharePoint session cookie went stale: a page visit renews it through SSO, then retry once
    await page.goto(P.site); await page.waitForTimeout(4000);
    page.__spDigest = null;
    return sp(page, P, method, path, body, { 'x-retried': '1' });
  }
  if (r.status() >= 400) throw new Error(`SharePoint ${method} ${path} -> ${r.status()} ${(await r.text()).slice(0, 200)}`);
  const t = await r.text(); try { return JSON.parse(t); } catch (e) { return null; }
}
const L = t => `lists/getbytitle('${encodeURIComponent(t)}')/items`;
async function spClear(page, P, list) {
  const items = (await sp(page, P, 'GET', `${L(list)}?$select=Id&$top=5000`)).value;
  for (const i of items) await sp(page, P, 'DELETE', `${L(list)}(${i.Id})`);
  return items.length;
}
async function spAdd(page, P, list, item) { return (await sp(page, P, 'POST', L(list), { Title: 'sandbox', ...item })).Id; }
async function spCount(page, P, list) { return (await sp(page, P, 'GET', `${L(list)}?$select=Id&$top=5000`)).value.length; }

// ---- runs ----
async function waitForFirstPoll(page, P, f, sinceIso, timeoutS) {
  const trig = ((await api(page, P, 'GET', `/flows/${f.id}/triggers`)).value || [])[0];
  if (!trig) throw new Error(`${f.name}: no trigger found`);
  const t0 = Date.now();
  while (Date.now() - t0 < timeoutS * 1000) {
    const h = ((await api(page, P, 'GET', `/flows/${f.id}/triggers/${trig.name}/histories?$top=5`)).value || [])
      .find(x => x.properties.startTime >= sinceIso);
    if (h) return h.properties.startTime;
    await page.waitForTimeout(5000);
  }
  throw new Error(`${f.name}: trigger did not poll within ${timeoutS}s of being switched on`);
}

async function waitForRun(page, P, f, sinceIso, timeoutS) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeoutS * 1000) {
    const runs = (await api(page, P, 'GET', `/flows/${f.id}/runs?$top=10`)).value || [];
    const r = runs.filter(x => x.properties.startTime >= sinceIso).sort((a, b) => a.properties.startTime.localeCompare(b.properties.startTime))[0];
    if (r && !['Running', 'Waiting'].includes(r.properties.status)) return r;
    await page.waitForTimeout(8000);
  }
  return null;
}

async function runDetail(page, P, f, run, countActions) {
  const acts = (await api(page, P, 'GET', `/flows/${f.id}/runs/${run.name}/actions`)).value || [];
  const failed = acts.filter(a => a.properties.status === 'Failed')
    .map(a => ({ action: a.name, code: a.properties.code, error: ((a.properties.error && a.properties.error.message) || '').slice(0, 300) }));
  const counts = {};
  for (const name of countActions || []) {
    const c = { Succeeded: 0, Failed: 0, Skipped: 0 };
    try {
      const reps = (await api(page, P, 'GET', `/flows/${f.id}/runs/${run.name}/actions/${encodeURIComponent(name)}/repetitions`)).value || [];
      for (const r of reps) {
        c[r.properties.status] = (c[r.properties.status] || 0) + 1;
        if (r.properties.status === 'Failed' && !c.firstError) c.firstError = ((r.properties.error && r.properties.error.message) || '').slice(0, 300);
      }
    } catch (e) { // not inside a loop: use the action's own status
      const a = acts.find(x => x.name === name); if (a) c[a.properties.status] = (c[a.properties.status] || 0) + 1;
    }
    counts[name] = c;
  }
  const post = acts.filter(a => /^Post_message/.test(a.name)).map(a => `${a.name}:${a.properties.status}`);
  return {
    run: run.name, status: run.properties.status, code: run.properties.code || null,
    runError: (run.properties.error && run.properties.error.message) || null,
    start: run.properties.startTime, failed, counts, teamsPosts: post,
    url: `${PA}/environments/${P.env}/flows/${f.id}/runs/${run.name}`,
  };
}

async function screenshotRun(page, url, path) {
  await page.goto(url);
  await page.waitForTimeout(12000);
  await page.getByRole('button', { name: 'Close' }).first().click({ timeout: 2000 }).catch(() => {});
  await page.waitForTimeout(800);
  await page.screenshot({ path });
}

// Leave a result where browser_evaluate(filename=...) can save it (scripts can't write files themselves).
async function publish(page, result) {
  await page.evaluate(r => { window.__pwResult = r; }, result).catch(() => {});
  return result;
}
