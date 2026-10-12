// Hartwood workshop planner. Everything lives in this browser (localStorage), with JSON backup export/import.
(function () {
  'use strict';
  const D = window.HW_DATA;
  const KEY = 'hw-planner-v1';
  const STAGES = [['queued', 'Waiting'], ['cut', 'Cut'], ['checked', 'Checked'], ['packed', 'Packed'], ['shipped', 'Shipped']];
  const $ = s => document.querySelector(s);
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const today = () => new Date().toISOString().slice(0, 10);
  const uid = () => Math.random().toString(36).slice(2, 9);

  // ---------------------------------------------------------------- state
  let mem = null;
  function blank() {
    return { orders: [], units: [], batches: [], stock: {}, defects: [], settings: { ...D.settings } };
  }
  function load() {
    try { mem = JSON.parse(localStorage.getItem(KEY)) || blank(); } catch { mem = mem || blank(); }
    mem.settings = { ...D.settings, ...(mem.settings || {}) };
    return mem;
  }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(mem)); } catch { toast('Could not save on this device: export a backup.'); } }
  const S = load();

  // ---------------------------------------------------------------- stock items: natural + one per sheet color
  const colors = {};
  Object.values(D.kits).forEach(k => k.sheets.forEach(s => { if (s.color !== 'natural') colors[s.color] = s.label; }));
  const ITEMS = {};
  Object.entries(D.items).forEach(([key, it]) => {
    if (key !== 'sheet_color') { ITEMS[key] = { ...it }; return; }
    // split colored sheets by color, reorder level by each color's share of weekly use
    const use = {}; let total = 0;
    Object.entries(D.kits).forEach(([kk, k]) => k.sheets.forEach(s => {
      if (s.color === 'natural') return;
      const u = s.fraction * (D.weekly_plan[kk] || 0); use[s.color] = (use[s.color] || 0) + u; total += u;
    }));
    Object.entries(colors).forEach(([c, label]) => {
      const share = total ? use[c] / total : 0;
      ITEMS['sheet_' + c] = { ...it, name: `${label} sheet 12 x 12 x 1/8 in`, reorder_at: Math.max(2, Math.ceil(it.reorder_at * share)),
        order_qty: Math.max(it.pack, Math.ceil(it.order_qty * share / it.pack) * it.pack) };
    });
  });
  function sheetNeeds(kitKey, n) {
    // physical sheets for n kits: full sheets n each; half and quarter tiles serve 2 or 4 kits
    const out = {};
    D.kits[kitKey].sheets.forEach(s => {
      const key = s.color === 'natural' ? 'sheet_natural' : 'sheet_' + s.color;
      out[key] = (out[key] || 0) + Math.ceil(n * s.fraction - 1e-9);
    });
    return out;
  }

  // ---------------------------------------------------------------- helpers
  function kitKey(name) {
    const n = String(name || '').trim().toLowerCase();
    return Object.keys(D.kits).find(k => D.kits[k].aliases.includes(n) || D.kits[k].name.toLowerCase() === n) || null;
  }
  function toast(msg) { const t = $('#toast'); t.textContent = msg; t.hidden = false; clearTimeout(t._h); t._h = setTimeout(() => { t.hidden = true; }, 2600); }
  function addOrder(o) {
    const k = kitKey(o.kit);
    if (!k) return false;
    const id = String(o.order_id || ('M' + (S.orders.length + 1001)));
    const qty = Math.max(1, parseInt(o.qty, 10) || 1);
    S.orders.push({ id, date: o.date || today(), kit: k, qty, customer: o.customer || '', channel: o.channel || 'own site' });
    for (let i = 0; i < qty; i++) S.units.push({ id: uid(), order: id, kit: k, stage: 'queued', batch: null });
    return true;
  }
  function parseCSV(text) {
    const rows = []; let row = [], cur = '', q = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (q) { if (c === '"' && text[i + 1] === '"') { cur += '"'; i++; } else if (c === '"') q = false; else cur += c; }
      else if (c === '"') q = true;
      else if (c === ',') { row.push(cur); cur = ''; }
      else if (c === '\n' || c === '\r') { if (c === '\r' && text[i + 1] === '\n') i++; row.push(cur); rows.push(row); row = []; cur = ''; }
      else cur += c;
    }
    if (cur || row.length) { row.push(cur); rows.push(row); }
    const head = rows.shift().map(h => h.trim().toLowerCase());
    return rows.filter(r => r.some(x => x.trim())).map(r => Object.fromEntries(head.map((h, i) => [h, (r[i] || '').trim()])));
  }

  // ---------------------------------------------------------------- tabs
  document.querySelectorAll('.tabs button').forEach(b => b.addEventListener('click', () => {
    document.querySelectorAll('.tabs button').forEach(x => x.setAttribute('aria-selected', String(x === b)));
    document.querySelectorAll('.panel').forEach(p => { p.hidden = p.id !== b.dataset.tab; });
    render();
  }));
  $('#modeTag').textContent = `color: ${D.color_mode === 'print' ? 'UV-printed' : 'pre-colored sheets'} · data ${D.generated}`;
  const kitOptions = Object.entries(D.kits).map(([k, v]) => `<option value="${k}">${esc(v.name)}</option>`).join('');
  $('#orderKit').innerHTML = kitOptions; $('#defectKit').innerHTML = kitOptions;
  $('#defectCat').innerHTML = D.defects.map(d => `<option value="${d.id}">${esc(d.label)}</option>`).join('');

  // ---------------------------------------------------------------- orders
  $('#orderForm').addEventListener('submit', e => {
    e.preventDefault(); const f = new FormData(e.target);
    addOrder({ kit: f.get('kit'), qty: f.get('qty'), customer: f.get('customer'), channel: f.get('channel') });
    save(); render(); toast('Order added'); e.target.reset();
  });
  $('#csvFile').addEventListener('change', async e => {
    const file = e.target.files[0]; if (!file) return;
    const rows = parseCSV(await file.text()); let ok = 0, bad = 0;
    rows.forEach(r => { if (addOrder(r)) ok++; else bad++; });
    save(); render(); toast(`${ok} orders imported${bad ? `, ${bad} skipped (unknown kit)` : ''}`); e.target.value = '';
  });
  function renderOrders() {
    const tb = $('#orderTable tbody');
    if (!S.orders.length) { tb.innerHTML = '<tr><td colspan="8" class="muted">No orders yet. Import a CSV or add one above.</td></tr>'; return; }
    tb.innerHTML = S.orders.slice().reverse().map(o => {
      const us = S.units.filter(u => u.order === o.id);
      const shipped = us.filter(u => u.stage === 'shipped').length;
      const pct = us.length ? Math.round(100 * us.reduce((a, u) => a + STAGES.findIndex(s => s[0] === u.stage), 0) / (us.length * 4)) : 0;
      return `<tr><td>${esc(o.id)}</td><td>${esc(o.date)}</td><td>${esc(D.kits[o.kit].name)}</td><td>${o.qty}</td><td>${esc(o.customer)}</td>
        <td>${esc(o.channel)}</td><td><div class="progress" title="${pct}%"><div style="width:${pct}%"></div></div><small>${shipped}/${us.length} shipped</small></td>
        <td><button class="btn small ghost" data-del="${esc(o.id)}" aria-label="Delete order ${esc(o.id)}">Delete</button></td></tr>`;
    }).join('');
    tb.querySelectorAll('[data-del]').forEach(b => b.addEventListener('click', () => {
      if (!confirm('Delete this order and its kits?')) return;
      S.orders = S.orders.filter(o => o.id !== b.dataset.del); S.units = S.units.filter(u => u.order !== b.dataset.del); save(); render();
    }));
  }

  // ---------------------------------------------------------------- cut queue + batches
  function queued() {
    const q = {}; S.units.filter(u => u.stage === 'queued' && !u.batch).forEach(u => { q[u.kit] = (q[u.kit] || 0) + 1; }); return q;
  }
  $('#startBatch').addEventListener('click', () => {
    const q = queued(); const keys = Object.keys(q);
    if (!keys.length) { toast('Nothing waiting to be cut'); return; }
    keys.forEach(k => {
      const n = q[k]; const id = 'B' + (S.batches.length + 1);
      const jobs = D.kits[k].jobs.map(j => ({ job: j.job, runs: Math.ceil(n / j.kits_per_run), done: 0, laser_min: j.laser_min, file: j.file }));
      S.batches.push({ id, kit: k, n, created: new Date().toISOString(), jobs, done: false });
      S.units.filter(u => u.kit === k && u.stage === 'queued' && !u.batch).forEach(u => { u.batch = id; });
    });
    save(); render(); toast('Batch created: run the jobs in the list');
  });
  function batchMinutes(b) {
    const swap = D.settings.swap_min_per_job;
    return b.jobs.reduce((a, j) => a + (j.runs - j.done) * (j.laser_min + swap), 0);
  }
  function finishBatch(b) {
    b.done = true;
    Object.entries(sheetNeeds(b.kit, b.n)).forEach(([key, n]) => { S.stock[key] = (S.stock[key] || 0) - n; });
    S.units.filter(u => u.batch === b.id && u.stage === 'queued').forEach(u => { u.stage = 'cut'; });
    toast(`Batch ${b.id} cut: ${b.n} kits moved to Cut, sheets taken out of stock`);
  }
  function renderQueue() {
    const q = queued();
    $('#queueSummary').innerHTML = Object.keys(D.kits).map(k => {
      const n = q[k] || 0; const needs = sheetNeeds(k, n);
      const mins = D.kits[k].jobs.reduce((a, j) => a + Math.ceil(n / j.kits_per_run) * (j.laser_min + D.settings.swap_min_per_job), 0);
      return `<div class="card qcard"><h3>${esc(D.kits[k].name)}</h3><div class="big">${n}</div><div class="muted">kits waiting</div>
        ${n ? `<ul class="sheetlist">${Object.entries(needs).map(([key, c]) => `<li>${c} x ${esc(ITEMS[key].name)}</li>`).join('')}</ul>
        <p class="muted">About ${Math.round(mins)} min on the laser</p>` : ''}</div>`;
    }).join('');
    const open = S.batches.filter(b => !b.done).concat(S.batches.filter(b => b.done).slice(-5).reverse());
    $('#batchList').innerHTML = open.length ? open.map(b => `<div class="card batch ${b.done ? 'done' : ''}">
      <div class="row-head"><h3>${b.id}: ${b.n} x ${esc(D.kits[b.kit].name)}</h3>
      <span class="pill ${b.done ? 'ok' : 'warn'}">${b.done ? '✓ cut' : '◷ ' + Math.round(batchMinutes(b)) + ' min left'}</span></div>
      ${b.jobs.map((j, i) => `<div class="job"><span class="runs">${j.done}/${j.runs} runs</span><span>${esc(j.job)}</span><code>${esc(j.file)}</code>
        ${b.done ? '' : `<button class="btn small" data-b="${b.id}" data-j="${i}">+1 run done</button>`}</div>`).join('')}
      ${b.done ? '' : `<p><button class="btn small primary" data-finish="${b.id}">All jobs done</button></p>`}</div>`).join('')
      : '<p class="muted">No batches yet.</p>';
    document.querySelectorAll('[data-j]').forEach(btn => btn.addEventListener('click', () => {
      const b = S.batches.find(x => x.id === btn.dataset.b); const j = b.jobs[+btn.dataset.j];
      j.done = Math.min(j.runs, j.done + 1);
      if (b.jobs.every(x => x.done >= x.runs)) finishBatch(b);
      save(); render();
    }));
    document.querySelectorAll('[data-finish]').forEach(btn => btn.addEventListener('click', () => {
      const b = S.batches.find(x => x.id === btn.dataset.finish); b.jobs.forEach(j => { j.done = j.runs; }); finishBatch(b); save(); render();
    }));
  }

  // ---------------------------------------------------------------- schedule
  $('#printSched').addEventListener('click', () => { $('#printDate').textContent = 'for ' + today(); window.print(); });
  function renderSchedule() {
    const st = S.settings; const [h, m] = st.shift_start.split(':').map(Number);
    const shiftMin = st.shift_hours * 60;
    const runs = [];
    S.batches.filter(b => !b.done).forEach(b => b.jobs.forEach(j => {
      for (let r = j.done; r < j.runs; r++) runs.push({ label: `${b.id} ${j.job}`, min: (j.laser_min + D.settings.swap_min_per_job) / st.efficiency });
    }));
    $('#schedHint').textContent = runs.length
      ? `${runs.length} laser runs, about ${Math.round(runs.reduce((a, r) => a + r.min, 0))} min including swaps at ${Math.round(st.efficiency * 100)}% efficiency. Shift ${st.shift_start}, ${st.shift_hours} h.`
      : 'Nothing to cut. Start a batch in the Cut queue.';
    let day = 0, t = 0; const days = [[]];
    runs.forEach(r => { if (t + r.min > shiftMin) { day++; t = 0; days.push([]); } days[day].push({ ...r, start: t }); t += r.min; });
    const fmt = mins => { const tt = h * 60 + m + mins; return `${String(Math.floor(tt / 60) % 24).padStart(2, '0')}:${String(Math.round(tt % 60)).padStart(2, '0')}`; };
    $('#timeline').innerHTML = runs.length ? days.map((d, i) => `<div class="day card"><h2>Day ${i + 1}</h2><div class="timeline">${d.map(r =>
      `<div class="slot"><span>${fmt(r.start)} to ${fmt(r.start + r.min)}</span><div><div class="jobname"><span class="tick" aria-hidden="true"></span>${esc(r.label)}
        <small>${Math.round(r.min)} min</small></div><div class="bar"><div style="left:${100 * r.start / shiftMin}%;width:${Math.max(1, 100 * r.min / shiftMin)}%"></div></div></div></div>`).join('')}</div></div>`).join('') : '';
  }

  // ---------------------------------------------------------------- tracking
  function renderBoard() {
    $('#board').innerHTML = STAGES.map(([s, label], i) => {
      const us = S.units.filter(u => u.stage === s);
      const next = STAGES[i + 1];
      return `<div class="col"><h3>${label}<span>${us.length}</span></h3>${us.slice(0, 60).map(u => {
        const o = S.orders.find(x => x.id === u.order);
        return `<button class="unit" ${next && s !== 'queued' ? `data-u="${u.id}"` : 'disabled'} aria-label="${esc(D.kits[u.kit].name)} for order ${esc(u.order)}${next && s !== 'queued' ? ': move to ' + next[1] : ''}">
          <b>${esc(D.kits[u.kit].name)}</b><small>Order ${esc(u.order)} ${o ? '· ' + esc(o.customer) : ''}${s === 'queued' ? (u.batch ? ' · in ' + u.batch : ' · not batched') : ''}</small></button>`;
      }).join('')}${us.length > 60 ? `<p class="muted">+ ${us.length - 60} more</p>` : ''}</div>`;
    }).join('');
    document.querySelectorAll('[data-u]').forEach(b => b.addEventListener('click', () => {
      const u = S.units.find(x => x.id === b.dataset.u); const i = STAGES.findIndex(s => s[0] === u.stage);
      u.stage = STAGES[i + 1][0];
      if (u.stage === 'packed') {
        Object.entries(D.kits[u.kit].bom).forEach(([key, q]) => { if (!key.startsWith('sheet')) S.stock[key] = (S.stock[key] || 0) - q; });
      }
      save(); render();
    }));
  }

  // ---------------------------------------------------------------- inventory
  function renderStock() {
    let low = 0;
    $('#stockTable tbody').innerHTML = Object.entries(ITEMS).map(([key, it]) => {
      const on = Math.round((S.stock[key] || 0) * 10) / 10;
      const st = on <= 0 ? ['bad', '✕ Out: order now'] : on <= it.reorder_at ? ['warn', '! Reorder now'] : ['ok', '✓ OK'];
      if (st[0] !== 'ok') low++;
      return `<tr><td>${esc(it.name)}<br><small class="muted">${esc(it.unit)} · lead ${it.lead_days} days</small></td>
        <td><input type="number" step="any" value="${on}" data-stock="${key}" aria-label="On hand: ${esc(it.name)}"></td>
        <td>${it.reorder_at}</td><td><span class="pill ${st[0]}">${st[1]}</span></td><td>${it.order_qty}</td>
        <td><small>${it.suppliers.map(s => esc(s.name) + ': ' + esc(s.price)).join('<br>')}</small></td>
        <td><button class="btn small" data-recv="${key}">+ received ${it.order_qty}</button></td></tr>`;
    }).join('');
    const badge = $('#stockBadge'); badge.hidden = !low; badge.textContent = low;
    document.querySelectorAll('[data-stock]').forEach(inp => inp.addEventListener('change', () => { S.stock[inp.dataset.stock] = parseFloat(inp.value) || 0; save(); renderStock(); }));
    document.querySelectorAll('[data-recv]').forEach(b => b.addEventListener('click', () => { const it = ITEMS[b.dataset.recv];
      S.stock[b.dataset.recv] = (S.stock[b.dataset.recv] || 0) + it.order_qty; save(); renderStock(); toast('Stock updated'); }));
  }

  // ---------------------------------------------------------------- quality: log + Pareto
  $('#defectForm').addEventListener('submit', e => {
    e.preventDefault(); const f = new FormData(e.target);
    S.defects.push({ date: today(), kit: f.get('kit'), code: f.get('code').toUpperCase(), cat: f.get('cat'), count: Math.max(1, +f.get('count') || 1), note: f.get('note') });
    save(); render(); toast('Logged'); e.target.reset();
  });
  $('#exportDefects').addEventListener('click', () => {
    const lines = [['date', 'kit', 'part', 'problem', 'count', 'note'].join(',')].concat(S.defects.map(d =>
      [d.date, D.kits[d.kit].name, d.code, D.defects.find(x => x.id === d.cat).label, d.count, d.note].map(v => `"${String(v).replace(/"/g, '""')}"`).join(',')));
    download('hartwood_quality_log.csv', lines.join('\n'), 'text/csv');
  });
  $('#paretoWin').addEventListener('change', () => renderQuality());
  function renderQuality() {
    const days = +$('#paretoWin').value, from = days ? new Date(Date.now() - days * 864e5).toISOString().slice(0, 10) : '';
    const win = S.defects.filter(d => d.date >= from);
    const tot = {}; win.forEach(d => { tot[d.cat] = (tot[d.cat] || 0) + d.count; });
    const rows = D.defects.map(d => ({ ...d, n: tot[d.id] || 0 })).filter(d => d.n > 0).sort((a, b) => b.n - a.n);
    const all = rows.reduce((a, r) => a + r.n, 0);
    $('#paretoRange').textContent = win.length ? `(${win[0].date} to ${win[win.length - 1].date}, ${all} problems)` : '';
    if (!rows.length) { $('#pareto').innerHTML = `<p class="muted">${S.defects.length ? 'No problems in this period.' : 'No problems logged yet.'}</p>`; $('#fixFirst').textContent = ''; }
    else {
      const W = 760, H = 300, pad = { l: 40, r: 10, t: 22, b: 70 }, bw = Math.min(110, (W - pad.l - pad.r) / rows.length), max = rows[0].n;
      let cum = 0;
      const bars = rows.map((r, i) => {
        cum += r.n; const x = pad.l + i * bw + 6, h = (H - pad.t - pad.b) * r.n / max, y = H - pad.b - h;
        const cp = Math.round(100 * cum / all);
        return `<g class="pbar" data-tip="${esc(r.label)}: ${r.n} (${Math.round(100 * r.n / all)}%), ${cp}% of all problems so far">
          <rect x="${x - 4}" y="${pad.t}" width="${bw - 4}" height="${H - pad.t - pad.b}" fill="transparent"/>
          <path d="M${x},${H - pad.b} V${y + 4} q0,-4 4,-4 H${x + bw - 16} q4,0 4,4 V${H - pad.b} Z" fill="var(--series-1)"/>
          <text x="${x + (bw - 12) / 2}" y="${y - 6}" text-anchor="middle" font-size="13" fill="#3A2A1F">${r.n}</text>
          <text x="${x + (bw - 12) / 2}" y="${H - pad.b + 18}" text-anchor="middle" font-size="12" fill="#52514e">${esc(r.id)}</text>
          <text x="${x + (bw - 12) / 2}" y="${H - pad.b + 36}" text-anchor="middle" font-size="11" fill="#52514e">${cp}% so far</text></g>`;
      }).join('');
      $('#pareto').innerHTML = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Pareto chart of problems by type">
        <line x1="${pad.l}" x2="${W - pad.r}" y1="${H - pad.b}" y2="${H - pad.b}" stroke="#c9c6bd"/>${bars}</svg>`;
      $('#fixFirst').textContent = `Fix first: ${rows[0].label} (${Math.round(100 * rows[0].n / all)}% of all problems).`;
      const tip = $('#tip');
      document.querySelectorAll('.pbar').forEach(g => {
        g.addEventListener('pointermove', e => { tip.hidden = false; tip.textContent = g.dataset.tip; tip.style.left = (e.clientX + 12) + 'px'; tip.style.top = (e.clientY + 12) + 'px'; });
        g.addEventListener('pointerleave', () => { tip.hidden = true; });
      });
    }
    $('#defectTable tbody').innerHTML = S.defects.slice().reverse().slice(0, 100).map((d, i) => `<tr><td>${esc(d.date)}</td><td>${esc(D.kits[d.kit].name)}</td>
      <td>${esc(d.code)}</td><td>${esc(D.defects.find(x => x.id === d.cat).label)}</td><td>${d.count}</td><td>${esc(d.note)}</td>
      <td><button class="btn small ghost" data-dd="${S.defects.length - 1 - i}">Delete</button></td></tr>`).join('') || '<tr><td colspan="7" class="muted">Nothing logged.</td></tr>';
    document.querySelectorAll('[data-dd]').forEach(b => b.addEventListener('click', () => { S.defects.splice(+b.dataset.dd, 1); save(); render(); }));
  }

  // ---------------------------------------------------------------- settings + backup
  const sf = $('#settingsForm');
  sf.shift_start.value = S.settings.shift_start; sf.shift_hours.value = S.settings.shift_hours; sf.efficiency.value = S.settings.efficiency;
  sf.addEventListener('submit', e => { e.preventDefault();
    S.settings.shift_start = sf.shift_start.value || '08:00'; S.settings.shift_hours = +sf.shift_hours.value || 8; S.settings.efficiency = +sf.efficiency.value || 0.85;
    save(); toast('Settings saved'); });
  function download(name, text, type) {
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([text], { type })); a.download = name; a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  }
  $('#exportAll').addEventListener('click', () => download(`hartwood_planner_${today()}.json`, JSON.stringify(S, null, 1), 'application/json'));
  $('#importAll').addEventListener('change', async e => {
    const f = e.target.files[0]; if (!f) return;
    try { const d = JSON.parse(await f.text()); Object.assign(S, blank(), d); save(); render(); toast('Backup loaded'); } catch { toast('That file is not a planner backup'); }
  });
  $('#resetAll').addEventListener('click', () => { if (confirm('Clear all orders, stock and logs on this tablet?')) { Object.assign(S, blank()); save(); render(); } });

  function render() { renderOrders(); renderQueue(); renderSchedule(); renderBoard(); renderStock(); renderQuality(); }
  render();
  window.HW_PLANNER = { state: S, addOrder, save, render };    // for tests
})();
