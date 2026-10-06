// Entry points for tools/sandbox/pw.py. Each takes (page, P) and returns a JSON-able result (also left on window.__pwResult).

async function cmd_flows(page, P) {
  const fl = (await listFlows(page, P)).filter(f => /^\[SANDBOX-/.test(f.name) && (!P.filter || f.name.toLowerCase().includes(P.filter.toLowerCase())));
  return publish(page, fl.sort((a, b) => a.name.localeCompare(b.name) || b.created.localeCompare(a.created)));
}

async function cmd_state(page, P) {
  const flows = await listFlows(page, P);
  const f = newest(flows, P.flowName);
  if (!f) throw new Error(`no flow named ${P.flowName}`);
  const twins = P.on ? await stopTwins(page, P, flows, f) : [];
  return publish(page, { flow: f.name, id: f.id, state: await setState(page, P, f, P.on), stoppedTwins: twins });
}

async function cmd_alloff(page, P) {
  const on = (await listFlows(page, P)).filter(f => /^\[SANDBOX-/.test(f.name) && f.state === 'Started');
  for (const f of on) await setState(page, P, f, false);
  const still = (await listFlows(page, P)).filter(f => /^\[SANDBOX-/.test(f.name) && f.state === 'Started').map(f => f.name);
  return publish(page, { stopped: on.map(f => f.name), stillOn: still });
}

async function cmd_import(page, P) {
  const before = new Date(Date.now() - 60000).toISOString();
  await page.goto(`${PA}/environments/${P.env}/flows/import`);
  const fr = page.locator('iframe[name="widgetIFrame"]').contentFrame();
  const input = fr.locator('input[type=file]');
  await input.waitFor({ state: 'attached', timeout: 60000 });
  await input.setInputFiles(P.zip);
  const rows = fr.locator('[role=row], tr');
  const flowRow = rows.filter({ hasText: '[SANDBOX-' }).first();
  await flowRow.waitFor({ timeout: 120000 });
  const flowText = (await flowRow.innerText()).replace(/\s+/g, ' ');
  if (!/Create as new/i.test(flowText)) throw new Error(`import setup is not "Create as new": ${flowText.slice(0, 160)}`);
  // connection rows come in a different order per package: pick each unset row by its text, not by position
  const done = [];
  for (let i = 0; i < 10; i++) {
    const pending = rows.filter({ hasText: 'Select during import' }).filter({ hasNotText: P.account });
    if (!(await pending.count())) break;
    const row = pending.first();
    const label = (await row.innerText()).replace(/\s+/g, ' ').replace(/\(select your own connection\)/i, '').replace(/Select during import.*/i, '').trim();
    await row.getByRole('button').first().click();
    const pick = fr.locator('pa-resource-list-picker').getByText(P.account).first();
    try { await pick.waitFor({ timeout: 15000 }); } catch (e) { throw new Error(`no connection of yours offered for "${label}": create or reconnect it first`); }
    await pick.click();
    await fr.getByRole('button', { name: 'Save', exact: true }).click();
    await page.waitForTimeout(1500);
    done.push(label);
  }
  const btn = fr.getByRole('button', { name: 'Import', exact: true });
  if (!(await btn.isEnabled())) throw new Error(`Import button still disabled after setting: ${done.join(', ')}`);
  await btn.click();
  let ok = false, t = '';
  for (let i = 0; i < 60 && !ok; i++) {
    await page.waitForTimeout(5000);
    t = await fr.locator('body').innerText().catch(() => '');
    ok = /successfully imported/i.test(t);
    if (/Import failed/i.test(t)) {
      const m = t.replace(/\s+/g, ' ').match(/Error (Flow save failed.*?)(?: Related resources|$)/);
      throw new Error(`import failed: ${m ? m[1].slice(0, 600) : t.replace(/\s+/g, ' ').slice(0, 400)}`);
    }
  }
  if (!ok) throw new Error(`import did not report success within 5 minutes; page says: ${t.replace(/\s+/g, ' ').slice(0, 300)}`);
  const f = (await listFlows(page, P)).filter(x => x.name === P.flowName && x.created >= before).sort((a, b) => b.created.localeCompare(a.created))[0];
  if (!f) throw new Error('imported, but the new flow was not found by name');
  if (f.state === 'Started') await setState(page, P, f, false);
  return publish(page, { imported: f.name, id: f.id, connections: done, state: 'Stopped' });
}

function check(expect, got) {
  if (!expect) return { pass: null, why: ['no expectation declared'] };
  const why = [];
  if (expect.status && expect.status !== got.status) why.push(`status ${got.status} != ${expect.status}`);
  if (expect.failedAction && !(got.failed || []).some(a => a.action === expect.failedAction)) why.push(`${expect.failedAction} did not fail`);
  for (const [act, want] of Object.entries(expect.counts || {})) {
    for (const [k, v] of Object.entries(want)) {
      const have = ((got.counts || {})[act] || {})[k] || 0;
      if (have !== v) why.push(`${act} ${k}=${have} != ${v}`);
    }
  }
  for (const [list, n] of Object.entries(expect.after || {})) if ((got.after || {})[list] !== n) why.push(`${list} has ${(got.after || {})[list]} != ${n}`);
  return { pass: why.length === 0, why };
}

async function cmd_run(page, P) {
  const S = P.scenario;
  const out = { flow: P.flowNo, package: P.pkg, scenario: S.name, at: new Date().toISOString() };
  const flows = await listFlows(page, P);
  const f = newest(flows, P.flowName);
  if (!f) throw new Error(`no flow named ${P.flowName}: import it first`);
  out.flowId = f.id;
  out.stoppedTwins = await stopTwins(page, P, flows, f);
  for (const list of S.clear || []) await spClear(page, P, list);
  for (const [list, items] of Object.entries(S.seed || {})) for (const it of items) await spAdd(page, P, list, it);
  await prepareFiles(page, P, S.stageOnly ? { ...S, upload: [] } : S); // stageOnly: the flow only reads the staged workbooks
  const started = new Date(Date.now() - 2000).toISOString();
  await setState(page, P, f, true);
  const since = new Date(Date.now() - 5000).toISOString();
  try {
    // a polling trigger's first check after switching on only sets its watermark: anything created before it is never
    // fired (observed 2026-10-02, flow 10 baseline). Wait for that first check before creating the trigger item.
    out.firstPoll = await waitForFirstPoll(page, P, f, started, 150);
    if (S.drop) { // file-trigger flows: drop real workbooks into the watched folder ({pkg} in a name = the package under test)
      const files = S.drop.map(u => ({ ...u, name: (u.name || u.file).replace('{pkg}', P.pkg) }));
      out.dropped = files.map(u => `${u.folder}/${u.name}`);
      await prepareFiles(page, P, { upload: files });
    } else await spAdd(page, P, P.triggerList, { Title: S.trigger || 'run' });
    const r = await waitForRun(page, P, f, since, S.timeout || P.timeout);
    if (!r) out.status = 'TIMEOUT';
    else Object.assign(out, await runDetail(page, P, f, r, S.count));
  } finally {
    out.finalState = await setState(page, P, f, false);
  }
  out.files = {};
  for (const rb of S.readback || []) out.files[`${rb.folder}/${rb.name}`] = await spBin(page, P, 'download', rb);
  out.after = {};
  for (const list of S.countLists || []) out.after[list] = await spCount(page, P, list);
  out.folders = {};
  for (const fo of S.inspect || []) out.folders[fo] = await spBin(page, P, 'list', { folder: fo });
  out.expected = (S.expect || {})[P.pkg] || null;
  Object.assign(out, check(out.expected, out));
  if (out.url && P.shot) { await screenshotRun(page, out.url, P.shot); out.screenshot = P.shot; }
  return publish(page, out);
}

// ---- file-trigger scenarios (harnesses): upload files over SharePoint REST, see which ones the flow processed ----
async function cmd_filetest(page, P) {
  const S = P.scenario;
  const base = P.site.replace(/^https?:\/\/[^/]+/, '').replace(/\/$/, '');
  const srv = p => `${base}${p}`.replace(/'/g, "''"); // a quote in a name must be doubled inside the OData url
  const H = { Accept: 'application/json;odata=nometadata' };
  const digest = async () => {
    const r = await page.request.post(`${P.site}/_api/contextinfo`, { headers: H });
    const t = await r.text();
    if (r.status() >= 400 || !t) throw new Error(`SharePoint contextinfo -> ${r.status()} (signed out of SharePoint?)`);
    return JSON.parse(t).FormDigestValue;
  };
  let dig = await digest();
  const post = async (path, data, extra) => {
    const r = await page.request.fetch(`${P.site}/_api/web/${path}`, { method: 'POST', headers: { ...H, 'X-RequestDigest': dig, ...(extra || {}) }, data });
    if (r.status() >= 400) throw new Error(`SharePoint POST ${path.slice(0, 80)} -> ${r.status()} ${(await r.text()).slice(0, 160)}`);
  };
  const files = async folder => {
    const r = await page.request.get(`${P.site}/_api/web/GetFolderByServerRelativeUrl('${srv(folder)}')/Files?$select=Name`, { headers: H });
    return r.status() === 200 ? (await r.json()).value.map(x => x.Name) : [];
  };
  const del = (folder, name) => post(`GetFileByServerRelativeUrl('${srv(folder)}/${name.replace(/'/g, "''")}')`, undefined, { 'IF-MATCH': '*', 'X-HTTP-Method': 'DELETE' });
  const ensureFolder = async folder => { try { await post(`folders/add('${srv(folder)}')`); } catch (e) { /* exists */ } };
  const folders = [...new Set([S.watched, ...(S.files || []).map(f => f.folder), S.archive])];
  for (const f of folders) await ensureFolder(f);
  for (const f of folders) for (const n of await files(f)) await del(f, n);
  for (const n of await files(S.copiesIn)) if (n.startsWith(S.copyPrefix)) await del(S.copiesIn, n);

  const flows = await listFlows(page, P);
  const f = newest(flows, P.flowName);
  if (!f) throw new Error(`no flow named ${P.flowName}: import it first`);
  const out = { flow: P.flowNo, package: P.pkg, scenario: S.name, at: new Date().toISOString(), flowId: f.id };
  out.stoppedTwins = await stopTwins(page, P, flows, f);
  const started = new Date(Date.now() - 2000).toISOString();
  await setState(page, P, f, true);
  try {
    out.firstPoll = await waitForFirstPoll(page, P, f, started, 150);
    const since = new Date(Date.now() - 5000).toISOString();
    for (const file of S.files) {
      await post(`GetFolderByServerRelativeUrl('${srv(file.folder)}')/Files/add(url='${file.name}',overwrite=true)`, 'x'.repeat(file.bytes || 2000), { 'Content-Type': 'application/octet-stream' });
      await page.waitForTimeout(3000);
    }
    const first = await waitForRun(page, P, f, since, P.timeout);
    out.firstRunStatus = first ? first.properties.status : 'NONE';
    await page.waitForTimeout((S.settle || 150) * 1000); // long enough for 2+ more polls, so "no run" means no run
    const runs = ((await api(page, P, 'GET', `/flows/${f.id}/runs?$top=20`)).value || []).filter(r => r.properties.startTime >= since);
    out.runs = runs.map(r => r.properties.status);
    out.status = runs.length ? runs.map(r => r.properties.status).join(',') : 'NO RUN';
  } finally {
    out.finalState = await setState(page, P, f, false);
  }
  out.copies = (await files(S.copiesIn)).filter(n => n.startsWith(S.copyPrefix));
  out.stillInWatched = {};
  for (const fo of [...new Set(S.files.map(x => x.folder))]) out.stillInWatched[fo] = await files(fo);
  out.archived = await files(S.archive);
  const why = [];
  if (out.runs.length !== S.expectRuns) why.push(`runs ${out.runs.length} != ${S.expectRuns}`);
  for (const file of S.files) {
    const copied = out.copies.includes(S.copyPrefix + file.name);
    if (copied !== file.expectProcessed) why.push(`${file.folder}/${file.name}: ${copied ? 'processed' : 'not processed'}, expected ${file.expectProcessed ? 'processed' : 'not processed'}`);
  }
  out.pass = why.length === 0; out.why = why;
  return publish(page, out);
}

// ---- binary files in the sandbox OneDrive (run inside the page, which has atob/fetch; the script sandbox has no Buffer) ----
async function spOrigin(page, P) {
  const origin = P.site.match(/^https?:\/\/[^/]+/)[0];
  // revisit the site every few minutes: after a long wait (e.g. a 15 minute run) the in-page fetches see a stale session
  // ("Unexpected end of JSON input" from contextinfo, observed 2026-10-06)
  const stale = !page.__spAt || Date.now() - page.__spAt > 5 * 60 * 1000;
  if (!page.url().startsWith(origin) || stale) { await page.goto(P.site); await page.waitForTimeout(3000); page.__spAt = Date.now(); }
}
async function spBin(page, P, op, args) {
  await spOrigin(page, P);
  const base = P.site.replace(/^https?:\/\/[^/]+/, '').replace(/\/$/, '');
  return page.evaluate(async ({ site, base, op, args }) => {
    const H = { Accept: 'application/json;odata=nometadata' };
    const q = s => s.replace(/'/g, "''");
    const dig = (await (await fetch(site + '/_api/contextinfo', { method: 'POST', headers: H })).json()).FormDigestValue;
    const folderUrl = f => `${site}/_api/web/GetFolderByServerRelativeUrl('${q(base + f)}')`;
    if (op === 'ensure') {
      let path = '';
      for (const seg of args.folder.split('/').filter(Boolean)) {
        path += '/' + seg;
        await fetch(`${site}/_api/web/folders/add('${q(base + path)}')`, { method: 'POST', headers: { ...H, 'X-RequestDigest': dig } });
      }
      return 'ok';
    }
    if (op === 'list') {
      const r = await fetch(`${folderUrl(args.folder)}/Files?$select=Name`, { headers: H });
      return r.status === 200 ? (await r.json()).value.map(x => x.Name) : [];
    }
    if (op === 'delete') {
      const r = await fetch(`${site}/_api/web/GetFileByServerRelativeUrl('${q(base + args.folder + '/' + args.name)}')`, { method: 'POST', headers: { ...H, 'X-RequestDigest': dig, 'IF-MATCH': '*', 'X-HTTP-Method': 'DELETE' } });
      return r.status;
    }
    if (op === 'upload') {
      const bin = Uint8Array.from(atob(args.b64), c => c.charCodeAt(0));
      const r = await fetch(`${folderUrl(args.folder)}/Files/add(url='${q(args.name)}',overwrite=true)`, { method: 'POST', headers: { ...H, 'X-RequestDigest': dig, 'Content-Type': 'application/octet-stream' }, body: bin });
      return r.status;
    }
    if (op === 'download') {
      const r = await fetch(`${site}/_api/web/GetFileByServerRelativeUrl('${q(base + args.folder + '/' + args.name)}')/$value`, { headers: H });
      if (r.status !== 200) return 'HTTP ' + r.status;
      const u8 = new Uint8Array(await r.arrayBuffer());
      let s = ''; for (let i = 0; i < u8.length; i += 8192) s += String.fromCharCode.apply(null, u8.subarray(i, i + 8192));
      return btoa(s);
    }
    throw new Error('unknown op ' + op);
  }, { site: P.site, base, op, args });
}
async function prepareFiles(page, P, S) {
  for (const fo of S.clearFolders || []) {
    await spBin(page, P, 'ensure', { folder: fo });
    // a delete of a workbook Excel Online still holds fails with 423 (observed 2026-10-02: a flow 12 raw file survived into the
    // flow 13 run and made it read the wrong columns): retry like uploads, then insist the folder really is empty
    for (let i = 0; i < 12; i++) {
      for (const n of await spBin(page, P, 'list', { folder: fo })) await spBin(page, P, 'delete', { folder: fo, name: n });
      if (!(await spBin(page, P, 'list', { folder: fo })).length) break;
      await page.waitForTimeout(10000);
    }
    const left = await spBin(page, P, 'list', { folder: fo });
    if (left.length) throw new Error(`could not empty ${fo}, still holds: ${left.join(', ')} (locked?)`);
  }
  for (const u of S.upload || []) {
    await spBin(page, P, 'ensure', { folder: u.folder });
    const b64 = u.b64 || (page.__pwFiles || {})[u.file];
    if (!b64) throw new Error(`no content for ${u.file}: run pw.py stage first (it keeps the workbooks on the page)`);
    let st = 0;
    for (let i = 0; i < 12; i++) { // 423 = the workbook is locked (Excel Online keeps a session open for a while after a flow used it)
      st = await spBin(page, P, 'upload', { folder: u.folder, name: u.name, b64 });
      if (st !== 423) break;
      await page.waitForTimeout(10000);
    }
    if (st >= 400) throw new Error(`upload of ${u.name} to ${u.folder} failed: HTTP ${st}`);
  }
}

// upload a scenario's workbooks without running anything (Power Automate validates Excel actions at import/save time, so the
// template workbooks must already exist in OneDrive before a real-Excel package is imported)
async function cmd_stage(page, P) {
  page.__pwFiles = { ...(page.__pwFiles || {}) };
  for (const u of [...P.scenario.upload, ...(P.scenario.drop || [])]) if (u.b64) page.__pwFiles[u.file] = u.b64; // later runs reference files by name only
  await prepareFiles(page, P, { upload: P.scenario.upload }); // `drop` files are only cached here: a run drops them into the watched folder
  return publish(page, { staged: P.scenario.upload.map(u => `${u.folder}/${u.name}`) });
}
