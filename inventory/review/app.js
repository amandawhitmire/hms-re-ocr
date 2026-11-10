const ITEMS = JSON.parse(document.getElementById('items').textContent);
const CROPS = JSON.parse(document.getElementById('crops').textContent);
const CHOICES = [
  { v: 'ocr_error', label: 'OCR error', short: 'OCR error', hint: 'page shows something other than what Vision read' },
  { v: 'on_page', label: 'On the page', short: 'On page', hint: 'Vision read it correctly; the author wrote it this way' },
  { v: 'not_a_name', label: 'Not a name', short: 'Not a name', hint: '' },
  { v: 'cant_tell', label: "Can't tell", short: "Can't tell", hint: '' },
];
const BANDS = [
  { id: 'low', label: 'Low confidence', note: 'Vision word confidence below 0.90' },
  { id: 'mid', label: 'Uncertain', note: 'confidence 0.90 to 0.95' },
  { id: 'high', label: 'High-confidence sample', note: '100 random flags at 0.95 and up' },
  { id: 'garbled', label: 'Heavily garbled', note: 'loose match only' },
];
const BAND_ORDER = Object.fromEntries(BANDS.map((b, i) => [b.id, i]));

// One card per paper + OCR reading + suggestion; every occurrence stays its own saved record.
const CARDS = [];
{
  const byKey = new Map();
  for (const it of ITEMS) {
    const key = it.druid + '|' + it.ocr + '|' + (it.suggestion || '');
    let c = byKey.get(key);
    if (!c) { c = { id: 'g-' + it.id, members: [] }; byKey.set(key, c); CARDS.push(c); }
    c.members.push(it);
  }
  for (const c of CARDS) {
    c.band = c.members.map(m => m.group).sort((a, b) => BAND_ORDER[a] - BAND_ORDER[b])[0];
    c.first = c.members[0];
  }
  CARDS.sort((a, b) => BAND_ORDER[a.band] - BAND_ORDER[b.band]);
}
const CARD_OF = {};
for (const c of CARDS) for (const m of c.members) CARD_OF[m.id] = c;

const state = { decisions: {}, filter: 'all', onlyOpen: false, focus: null, db: null, uid: null, saving: {}, editable: true };
const $ = (s, el = document) => el.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const dec = id => state.decisions[id] || {};
const linked = c => c.members.filter(m => !dec(m.id).separate);
const cardDone = c => c.members.every(m => dec(m.id).decision);
// the card-level value of a field: shared by every linked occurrence, else '' (mixed)
function shared(c, f) {
  const L = linked(c); if (!L.length) return '';
  const v = dec(L[0].id)[f];
  return L.every(m => (dec(m.id)[f] || '') === (v || '')) ? v : '';
}
const mixed = (c, f) => { const L = linked(c); return L.length > 1 && new Set(L.map(m => dec(m.id)[f] || '')).size > 1; };

function diffMarkup(a, b) {
  const n = a.length, m = b.length, L = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
  for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--)
    L[i][j] = a[i] === b[j] ? L[i + 1][j + 1] + 1 : Math.max(L[i + 1][j], L[i][j + 1]);
  let i = 0, j = 0, out = '', run = '';
  const flush = () => { if (run) { out += '<mark>' + esc(run) + '</mark>'; run = ''; } };
  while (i < n) {
    if (j < m && a[i] === b[j]) { flush(); out += esc(a[i]); i++; j++; }
    else if (j < m && L[i][j + 1] >= L[i + 1][j]) { j++; }
    else { run += a[i]; i++; }
  }
  flush();
  return out;
}

function visible() {
  return CARDS.filter(c => (state.filter === 'all' || c.band === state.filter) && (!state.onlyOpen || !cardDone(c)));
}

function renderFilters() {
  const all = [{ id: 'all', label: 'All' }, ...BANDS];
  $('#filters').innerHTML = all.map(b => {
    const cs = CARDS.filter(c => b.id === 'all' || c.band === b.id);
    return `<button class="chip" type="button" data-g="${b.id}" aria-pressed="${state.filter === b.id}">${esc(b.label)} ${cs.filter(cardDone).length}/${cs.length}</button>`;
  }).join('');
  const by = v => ITEMS.filter(it => dec(it.id).decision === v).length;
  const decided = ITEMS.filter(it => dec(it.id).decision).length;
  $('#progress-label').innerHTML = `<strong>${CARDS.filter(cardDone).length}</strong> of ${CARDS.length} cards done · ${decided} of ${ITEMS.length} occurrences · OCR error ${by('ocr_error')} · on the page ${by('on_page')} · not a name ${by('not_a_name')} · can't tell ${by('cant_tell')}`;
  const colors = { ocr_error: 'var(--s-error)', on_page: 'var(--s-page)', not_a_name: 'var(--s-notname)', cant_tell: 'var(--s-unsure)' };
  $('#meter').innerHTML = CHOICES.map(c => `<span style="width:${(100 * by(c.v) / ITEMS.length).toFixed(2)}%;background:${colors[c.v]}"></span>`).join('');
}

function clipHTML(c, m) {
  const d = dec(m.id), multi = c.members.length > 1, sep = !!d.separate;
  const ptype = m.pageType.startsWith('sparse') ? 'figure / table / short page' : 'text page';
  const badge = d.decision ? `<span class="badge" data-v="${esc(d.decision)}">${esc(CHOICES.find(x => x.v === d.decision)?.short || '')}</span>` : '';
  return `<figure class="clip${sep ? ' separate' : ''}" data-m="${esc(m.id)}">
    <div class="scan"><img data-id="${esc(m.id)}" alt="Page image region for ${esc(m.ocr)} on ${esc(m.page)}" loading="lazy"></div>
    <figcaption>
      <span class="cap-line"><b>${esc(m.page.split('_').pop())}</b> · conf <span class="mono">${m.wc.toFixed(2)}</span> · ${ptype} · <a href="${esc(m.fullPage)}" target="_blank" rel="noopener">full page</a></span>
      ${multi ? `<span class="cap-line">${badge}<button type="button" class="linkish sep-toggle" aria-pressed="${sep}">${sep ? 'Decide with the others' : 'Decide this one separately'}</button></span>` : ''}
      ${sep ? `<div class="mini" role="group" aria-label="Choice for page ${esc(m.page)}">
          ${CHOICES.map(ch => `<button type="button" class="choice mini-choice" data-v="${ch.v}" aria-pressed="${d.decision === ch.v}">${esc(ch.short)}</button>`).join('')}
        </div>
        <label class="sr" for="ms-${esc(m.id)}">Page shows</label>
        <input class="name-input mini-input" id="ms-${esc(m.id)}" data-mf="pageShows" value="${esc(d.pageShows || '')}" placeholder="Page shows (blank = ${esc(m.suggestion || 'closest name')})">` : ''}
    </figcaption>
  </figure>`;
}

function cardHTML(c) {
  const it = c.first, n = c.members.length, L = linked(c);
  const cd = shared(c, 'decision'), mx = mixed(c, 'decision');
  const useClosest = !!shared(c, 'useClosest');
  const bands = [...new Set(c.members.map(m => m.group))];
  const countNote = n > 1
    ? `<p class="repeat">Same reading on <b>${n} pages</b> of this paper. A choice applies to every clip except those you decide separately.${bands.length > 1 ? ' Clips fall in more than one confidence band.' : ''}</p>` : '';
  return `<article class="card${n > 1 ? ' multi' : ''}" tabindex="0" id="c-${esc(c.id)}" data-card="${esc(c.id)}" ${cardDone(c) ? 'data-done' : ''}>
    <div class="clips${n > 3 ? ' many' : ''}">${c.members.map(m => clipHTML(c, m)).join('')}</div>
    <div class="body">
      <dl class="readings">
        <dt>OCR read</dt><dd class="ocr">${diffMarkup(it.ocr, it.suggestion || it.ocr)}</dd>
        <dt>Closest name</dt><dd class="sugg">${esc(it.suggestion || '—')}</dd>
      </dl>
      <div class="meta"><span>${esc(it.druid)}</span><span>${esc(it.year)}</span>${n > 1 ? `<span>${n} occurrences</span>` : `<span>${esc(it.page)}</span>`}</div>
      <p class="paper">${esc(it.title)}</p>
      ${countNote}
      <div class="links"><a href="https://purl.stanford.edu/${esc(it.druid)}" target="_blank" rel="noopener">Paper in SearchWorks</a></div>
      ${L.length ? `
      <div class="choices" role="group" aria-label="What do the pages show?">
        ${CHOICES.map((ch, k) => `<button type="button" class="choice card-choice" data-v="${ch.v}" aria-pressed="${cd === ch.v}" title="${esc(ch.hint)}"><kbd>${k + 1}</kbd>${esc(ch.label)}</button>`).join('')}
      </div>
      ${mx ? `<p class="mixed">The linked clips have different choices. Picking one here sets them all.</p>` : ''}
      <div class="search-name">
        <button type="button" class="closest" aria-pressed="${useClosest}"><span class="tick" aria-hidden="true">${useClosest ? '✓' : ''}</span><kbd>5</kbd>Use closest name for search</button>
        <label for="pref-${esc(c.id)}" class="small">Or type a different name to use for search</label>
        <input class="name-input" id="pref-${esc(c.id)}" data-f="preferredName" value="${esc(shared(c, 'preferredName') || '')}" placeholder="${esc(it.suggestion || '')}">
      </div>
      <div class="fields">
        <label for="shows-${esc(c.id)}">Page shows (leave blank if it matches the closest name)</label>
        <input class="name-input" id="shows-${esc(c.id)}" data-f="pageShows" value="${esc(shared(c, 'pageShows') || '')}" placeholder="${esc(it.suggestion || '')}">
        <label for="note-${esc(c.id)}">Note</label>
        <input id="note-${esc(c.id)}" data-f="note" value="${esc(shared(c, 'note') || '')}" placeholder="handwritten, underlined, rotated, cut off…">
      </div>` : `<p class="mixed">Every clip on this card is decided separately.</p>`}
      <div class="status" id="st-${esc(c.id)}">${cardDone(c) ? 'Saved' : ''}</div>
    </div>
  </article>`;
}

const io = 'IntersectionObserver' in window ? new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { show(e.target); io.unobserve(e.target); } }), { rootMargin: '800px 0px' }) : null;
function show(img) { const b = CROPS[img.dataset.id]; if (b && !img.src) img.src = 'data:image/jpeg;base64,' + b; }
function hydrate(root) { root.querySelectorAll('.scan img[data-id]').forEach(img => io ? io.observe(img) : show(img)); }

function renderList() {
  const cards = visible();
  if (!cards.length) { $('#list').innerHTML = `<p class="empty">Nothing left in this view. Pick another group or turn off “Undecided only”.</p>`; return; }
  let html = '', last = null;
  for (const c of cards) {
    if (c.band !== last) { const b = BANDS.find(b => b.id === c.band); html += `<h2 class="group-head">${esc(b.label)} <small>${esc(b.note)}</small></h2>`; last = c.band; }
    html += cardHTML(c);
  }
  $('#list').innerHTML = html;
  hydrate($('#list'));
  if (state.focus) $('#c-' + CSS.escape(state.focus))?.classList.add('focused');
}

// Re-render one card, unless the viewer is typing in it (then only its buttons update).
function refreshCard(c, force = false) {
  const el = $('#c-' + CSS.escape(c.id)); if (!el) return;
  if (!force && el.contains(document.activeElement) && document.activeElement.tagName === 'INPUT') {
    const cd = shared(c, 'decision');
    el.querySelectorAll('.card-choice').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.v === cd)));
    return;
  }
  const status = $('#st-' + CSS.escape(c.id))?.textContent;
  const tmp = document.createElement('div'); tmp.innerHTML = cardHTML(c);
  const fresh = tmp.firstElementChild;
  if (state.focus === c.id) fresh.classList.add('focused');
  el.replaceWith(fresh); hydrate(fresh);
  if (status && status !== 'Saved') setStatus(c.id, status);
}
function setStatus(cid, text) { const s = $('#st-' + CSS.escape(cid)); if (s) s.textContent = text; }

async function writeOne(id) {
  const it = ITEMS.find(x => x.id === id), cur = dec(id);
  const body = { decision: cur.decision || '', pageShows: cur.pageShows || '', note: cur.note || '',
    useClosest: !!cur.useClosest, preferredName: cur.preferredName || '', separate: !!cur.separate,
    page: it.page, druid: it.druid, ocr: it.ocr, suggestion: it.suggestion || '', group: it.group,
    updatedAt: new Date().toISOString(), by: state.uid || '' };
  state.saving[id] = body;
  if (state.saving[id + ':busy']) return;
  state.saving[id + ':busy'] = true;
  try {
    while (state.saving[id]) { const b = state.saving[id]; state.saving[id] = null; await state.db.collection('decisions').doc(id).set(b); }
  } finally { state.saving[id + ':busy'] = false; }
}

// Apply a patch to some occurrences, save each one in turn, and report on the card.
async function save(c, ids, patch) {
  for (const id of ids) state.decisions[id] = { ...dec(id), ...patch };
  refreshCard(c); renderFilters();
  if (!state.db) { setStatus(c.id, 'Not saved: saving is unavailable in this view'); return; }
  setStatus(c.id, ids.length > 1 ? `Saving ${ids.length} occurrences…` : 'Saving…');
  try { for (const id of ids) await writeOne(id); setStatus(c.id, 'Saved'); }
  catch (e) { setStatus(c.id, e?.code === 'invalid_argument' ? 'Not saved: you can view this page but not change it' : 'Not saved: the save failed. Choose again to retry.'); }
}

function focusCard(cid, scroll = true) {
  document.querySelectorAll('.card.focused').forEach(x => x.classList.remove('focused'));
  state.focus = cid;
  const el = $('#c-' + CSS.escape(cid));
  if (el) { el.classList.add('focused'); if (scroll) el.scrollIntoView({ block: 'center', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' }); el.focus({ preventScroll: true }); }
}
function step(dir) {
  const ids = visible().map(c => c.id); if (!ids.length) return;
  const k = ids.indexOf(state.focus);
  focusCard(ids[k < 0 ? 0 : Math.min(ids.length - 1, Math.max(0, k + dir))]);
}
function nextOpen(fromId) {
  const cs = visible(); const k = cs.findIndex(c => c.id === fromId);
  const rest = cs.slice(k + 1).concat(cs.slice(0, k + 1));
  const nxt = rest.find(c => !cardDone(c));
  if (nxt) focusCard(nxt.id);
}
const cardById = cid => CARDS.find(c => c.id === cid);

function decideCard(c, v) {
  const L = linked(c); if (!L.length) return;
  const off = shared(c, 'decision') === v && !mixed(c, 'decision');
  save(c, L.map(m => m.id), { decision: off ? '' : v });
  if (!off) {
    if (state.onlyOpen && cardDone(c)) setTimeout(() => { const ids = visible().map(x => x.id); renderList(); const n = ids.find(x => x !== c.id && !cardDone(cardById(x))); if (n) focusCard(n); }, 250);
    else if (cardDone(c)) nextOpen(c.id);
  }
}
function decideOne(c, id, v) { save(c, [id], { decision: dec(id).decision === v ? '' : v }); }
function toggleClosest(c) {
  const L = linked(c); if (!L.length) return;
  const on = !shared(c, 'useClosest');
  save(c, L.map(m => m.id), on ? { useClosest: true, preferredName: '' } : { useClosest: false });
}
function toggleSeparate(c, id) {
  const now = !dec(id).separate;
  if (now) { save(c, [id], { separate: true }); return; }
  // rejoining: take the card's current values so the clip agrees with the others
  const L = linked(c), src = L.length ? dec(L[0].id) : {};
  save(c, [id], { separate: false, decision: src.decision || dec(id).decision || '', pageShows: src.pageShows || '', note: src.note || '', useClosest: !!src.useClosest, preferredName: src.preferredName || '' });
}

document.addEventListener('click', e => {
  const chip = e.target.closest('.chip');
  if (chip) { state.filter = chip.dataset.g; renderFilters(); renderList(); return; }
  const cardEl = e.target.closest('.card'); if (!cardEl) return;
  const c = cardById(cardEl.dataset.card); state.focus = c.id;
  const clip = e.target.closest('.clip');
  if (e.target.closest('.sep-toggle')) { toggleSeparate(c, clip.dataset.m); return; }
  const mini = e.target.closest('.mini-choice');
  if (mini) { decideOne(c, clip.dataset.m, mini.dataset.v); return; }
  const btn = e.target.closest('.card-choice');
  if (btn) { decideCard(c, btn.dataset.v); return; }
  if (e.target.closest('.closest')) { toggleClosest(c); return; }
  if (!e.target.closest('a,input,button')) focusCard(c.id, false);
});
const timers = {};
document.addEventListener('input', e => {
  const inp = e.target.closest('input[data-f],input[data-mf]'); if (!inp) return;
  const c = cardById(inp.closest('.card').dataset.card);
  const clip = inp.closest('.clip');
  const f = inp.dataset.f || inp.dataset.mf, val = inp.value;
  const ids = clip ? [clip.dataset.m] : linked(c).map(m => m.id);
  const patch = f === 'preferredName' && val.trim() ? { [f]: val, useClosest: false } : { [f]: val };
  for (const id of ids) state.decisions[id] = { ...dec(id), ...patch };
  if (patch.useClosest === false) { const b = inp.closest('.card').querySelector('.closest'); if (b) { b.setAttribute('aria-pressed', 'false'); b.querySelector('.tick').textContent = ''; } }
  const key = c.id + (clip ? clip.dataset.m : '') + f;
  clearTimeout(timers[key]); setStatus(c.id, 'Typing…');
  timers[key] = setTimeout(() => save(c, ids, patch), 700);
});
document.addEventListener('focusin', e => { const el = e.target.closest('.card'); if (el && el.dataset.card !== state.focus) { document.querySelectorAll('.card.focused').forEach(x => x.classList.remove('focused')); state.focus = el.dataset.card; el.classList.add('focused'); } });
document.addEventListener('keydown', e => {
  if (e.target.closest('input') || e.metaKey || e.ctrlKey || e.altKey) return;
  const c = state.focus && cardById(state.focus);
  if (e.key === 'j') { e.preventDefault(); step(1); }
  else if (e.key === 'k') { e.preventDefault(); step(-1); }
  else if (/^[1-4]$/.test(e.key) && c) { e.preventDefault(); decideCard(c, CHOICES[+e.key - 1].v); }
  else if (e.key === '5' && c) { e.preventDefault(); toggleClosest(c); }
});
$('#only-open').addEventListener('change', e => { state.onlyOpen = e.target.checked; renderList(); });
$('#copy-csv').addEventListener('click', async e => {
  const cols = ['page', 'druid', 'group', 'ocr', 'suggestion', 'wc', 'decision', 'pageShows', 'searchName', 'note', 'decidedSeparately'];
  const q = v => '"' + String(v ?? '').replace(/"/g, '""') + '"';
  const lines = [cols.join(',')].concat(ITEMS.map(it => { const d = dec(it.id); const sn = d.preferredName || (d.useClosest ? it.suggestion : ''); return [it.page, it.druid, it.group, it.ocr, it.suggestion, it.wc, d.decision, d.pageShows, sn, d.note, d.separate ? 'yes' : ''].map(q).join(','); }));
  const btn = e.currentTarget;
  try { await navigator.clipboard.writeText(lines.join('\n')); btn.textContent = 'Copied'; }
  catch { btn.textContent = 'Copy failed'; }
  setTimeout(() => { btn.textContent = 'Copy results as CSV'; }, 1800);
});

function notice(text) { const n = $('#notice'); n.textContent = text; n.hidden = !text; }

renderFilters(); renderList();

(async () => {
  const db = await window.claude?.use?.('db');
  if (!db) { notice('Saving is unavailable in this view, so choices made here will be lost when you close the page. Open the page signed in to claude.ai to save them.'); renderFilters(); return; }
  state.db = db;
  try { const user = await window.claude.use('user'); state.uid = user ? await user.id() : null;
        if (user && (await user.can('data.write')) === false) notice('You can view these choices but not change them.'); } catch {}
  const timer = setTimeout(() => notice('Saved choices cannot be reached yet. New choices will save once the connection returns.'), 10000);
  db.collection('decisions').limit(1000).onSnapshot(snap => {
    if (!snap.metadata.fromCache) { clearTimeout(timer); if ($('#notice').textContent.startsWith('Saved choices cannot')) notice(''); }
    const touched = new Set();
    for (const ch of snap.docChanges()) {
      const id = ch.doc.id; if (!CARD_OF[id]) continue;
      if (ch.type === 'removed') delete state.decisions[id];
      else if (!state.saving[id + ':busy']) { const d = ch.doc.data(); state.decisions[id] = { decision: d.decision, pageShows: d.pageShows, note: d.note, useClosest: !!d.useClosest, preferredName: d.preferredName || '', separate: !!d.separate }; }
      touched.add(CARD_OF[id]);
    }
    touched.forEach(c => refreshCard(c));
    renderFilters();
  }, err => { clearTimeout(timer); notice('Saved choices could not be loaded (' + err.code + '). Reload the page to try again.'); });
})();
