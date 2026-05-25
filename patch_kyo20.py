import re

with open(r'c:\Users\TheVaner\Desktop\KYO2.0\kyo20.html', 'r', encoding='utf-8') as f:
    html = f.read()

# ── 1. CSS ────────────────────────────────────────────────────────────────────
CSS_ANCHOR = '  .kasa-ctx-separator { height: 1px; background: rgba(71,85,105,0.4); margin: 4px 0; }'
HISSE_CSS = r"""  .hisse-th {
    padding: 10px 14px; font-size: 11px; font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.06em; color: #34d399; white-space: nowrap; font-weight: 600;
    border-bottom: 1px solid rgba(71,85,105,0.45); background: rgba(15,23,42,0.7);
    cursor: pointer; user-select: none;
  }
  .hisse-th:hover { color: #6ee7b7; }
  .hisse-th.dim { color: #334155; cursor: default; }
  .hisse-td { padding: 10px 14px; font-size: 13px; white-space: nowrap; }
  .hisse-row { border-bottom: 1px solid rgba(71,85,105,0.18); transition: background 0.12s; }
  .pos { color: #34d399; }
  .neg { color: #f87171; }
  .neu { color: #94a3b8; }
  .btn-refresh {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 7px 14px; border-radius: 8px; font-size: 13px;
    font-family: 'JetBrains Mono', monospace;
    background: rgba(16,185,129,0.1); border: 1px solid rgba(52,211,153,0.3);
    color: #6ee7b7; transition: background 0.15s;
  }
  .btn-refresh:hover { background: rgba(16,185,129,0.25); }
  .btn-refresh:disabled { opacity: 0.45; cursor: not-allowed; }
  .progress-bar-wrap { height: 3px; background: rgba(71,85,105,0.3); border-radius: 2px; overflow: hidden; }
  .progress-bar-fill { height: 100%; background: linear-gradient(90deg,#10b981,#34d399); border-radius: 2px; transition: width 0.3s ease; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .spinning { animation: spin 0.8s linear infinite; }
"""
html = html.replace(CSS_ANCHOR, HISSE_CSS + CSS_ANCHOR)
print('CSS:', 'OK' if HISSE_CSS[:20] in html else 'FAIL')

# ── 2. Nav — remove hisse redirect ───────────────────────────────────────────
OLD_NAV = "      if (target === 'hisse') { window.location.href = 'hisse.html'; return; }\n"
html = html.replace(OLD_NAV, '')
print('Nav redirect removed:', OLD_NAV[:30] not in html)

# ── 3. HİSSE HTML section — insert before </main> ────────────────────────────
MIDAS_END = '    </section>\n   </main><!-- Bottom-Left Navigation -->'
HISSE_SECTION = """    </section>
    <!-- HİSSE PAGE -->
    <section id="page-hisse" class="page flex-col gap-4 w-full">
      <div class="flex items-center justify-between flex-wrap gap-3">
        <h2 class="text-2xl font-bold tracking-widest" style="color:#34d399;text-shadow:0 0 10px #34d399,0 0 24px #10b981">HİSSE</h2>
        <div class="flex items-center gap-2 flex-wrap">
          <div style="position:relative;display:inline-flex;align-items:center">
            <i data-lucide="search" style="width:13px;height:13px;color:#475569;position:absolute;left:10px;pointer-events:none"></i>
            <input id="hisse-search" type="text" placeholder="Sembol veya şirket..." maxlength="30"
              oninput="hisseFilter()" autocomplete="off" spellcheck="false"
              class="mono"
              style="padding:8px 12px 8px 30px;font-size:12px;background:rgba(15,23,42,0.8);border:1px solid rgba(71,85,105,0.6);color:#e2e8f0;outline:none;width:220px;border-radius:8px;text-transform:uppercase;transition:border-color 0.15s"
              onfocus="this.style.borderColor='rgba(52,211,153,0.6)'" onblur="this.style.borderColor='rgba(71,85,105,0.6)'" />
          </div>
          <span id="hisse-count" class="mono" style="font-size:11px;color:#334155"></span>
          <span id="hisse-status" class="mono" style="font-size:11px;color:#475569">–</span>
          <button id="hisse-refresh-btn" onclick="hisseFetchAll()" class="btn-refresh">
            <i data-lucide="refresh-cw" id="hisse-refresh-icon" class="w-4 h-4"></i>
            Yenile
          </button>
          <div class="flex items-center gap-1 px-3 py-2 rounded-lg mono" style="background:rgba(15,23,42,0.6);border:1px solid rgba(71,85,105,0.5)">
            <i data-lucide="clock" style="width:13px;height:13px;color:#475569"></i>
            <span id="hisse-timer" class="mono" style="font-size:11px;color:#64748b;margin-left:4px">–</span>
          </div>
        </div>
      </div>
      <div class="progress-bar-wrap" id="hisse-progress-wrap" style="display:none">
        <div class="progress-bar-fill" id="hisse-progress-bar" style="width:0%"></div>
      </div>
      <div style="border-radius:12px;overflow:hidden;border:1px solid rgba(71,85,105,0.35);background:rgba(10,14,26,0.6)">
        <div style="overflow-x:auto;width:100%">
          <table style="width:100%;border-collapse:collapse;table-layout:auto">
            <thead>
              <tr>
                <th class="hisse-th dim" style="text-align:center;width:40px">#</th>
                <th class="hisse-th" style="text-align:left" onclick="toggleSort('sym')"><span id="sort-sym">SEMBOL</span></th>
                <th class="hisse-th" style="text-align:left" onclick="toggleSort('name')"><span id="sort-name">ŞİRKET</span></th>
                <th class="hisse-th" style="text-align:right" onclick="toggleSort('price')"><span id="sort-price">FİYAT (₺)</span></th>
                <th class="hisse-th" style="text-align:right" onclick="toggleSort('chg')"><span id="sort-chg">DEĞİŞİM</span></th>
                <th class="hisse-th" style="text-align:right" onclick="toggleSort('pct')"><span id="sort-pct">DEĞ.%</span></th>
                <th class="hisse-th" style="text-align:right" onclick="toggleSort('vol')"><span id="sort-vol">HACİM</span></th>
                <th class="hisse-th dim" style="text-align:center">SAAT</th>
              </tr>
            </thead>
            <tbody id="hisse-tbody">
              <tr><td colspan="8" class="mono" style="padding:48px 16px;text-align:center;color:#334155;font-size:13px">Yükleniyor...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>
   </main><!-- Bottom-Left Navigation -->"""
html = html.replace(MIDAS_END, HISSE_SECTION)
print('Hisse section:', 'page-hisse' in html)

# ── 4. HİSSE JavaScript — insert before lucide.createIcons() ─────────────────
LUCIDE_CALL = '  lucide.createIcons();\n\n  // Initialize Element SDK'
HISSE_JS = r"""
  // ══════════════════════════════════════════════════════════════
  //  HİSSE — BIST Hisse Takip
  // ══════════════════════════════════════════════════════════════
  const BIST_ALL = [
    'AEFES','AFYON','AGESA','AGHOL','AKENR','AKBNK','AKCNS','AKFGY','AKFIN','AKGRT',
    'AKINV','AKSA','AKSEN','AKSGY','AKSUE','AKTIF','AKYHO','ALARK','ALBRK','ALCAR',
    'ALCTL','ALFAS','ALKIM','ALKLC','ALMAD','ALTNS','ALTNY','ALYAG','ANACM','ANELE',
    'ANHYT','ANSGR','ARCLK','ARDYZ','ARENA','ARSAN','ASCEL','ASELS','ASLAN','ASTOR',
    'ASUZU','ATAGY','ATATP','ATEKS','ATLAS','AVGYO','AVHOL','AVOD','AYCES','AYES',
    'BAGFS','BASCM','BASGZ','BASMA','BAYRK','BERA','BFREN','BIMAS','BIOEN','BIYOT',
    'BJKAS','BLCYT','BMEKS','BMSCH','BNTAS','BORLS','BORSK','BOSSA','BRISA','BRKO',
    'BRKVY','BRMEN','BRNKS','BRYAT','BSOKE','BTCIM','BUCIM','BURCE','BURVA','BUYUK',
    'CCOLA','CELHA','CEMTS','CEOEM','CIMSA','CLEBI','COIAC','CONSE','COSMO','CRDFA',
    'CRFSA','CSGYO','CUSAN',
    'DAGHL','DAGI','DAPGM','DARDL','DENGE','DESA','DESPC','DEVA','DEYLM','DGATE',
    'DGGYO','DITAS','DIVO','DMSAS','DNISI','DOAS','DOBUR','DOFER','DOGUB','DOKTA',
    'DOHOL','DORTS','DURDO','DYOBY','DZGYO',
    'ECILC','ECZYT','EDATA','EDIP','EGEEN','EGEPO','EGPRO','EGSER','EKSUN','EKTES',
    'EMKEL','EMNIS','ENKAI','ENSEN','EPLAS','ERBOS','ERCB','ERDMR','EREGL','ERGLI',
    'ESCAR','ESCOM','ESEN','ETGRI','ETYAK','EUHOL','EUPWR','EUREN','EUYO','EYGYO',
    'FADE','FENER','FMIZP','FORMT','FONET','FORTE','FROTO','FZLGY',
    'GARAN','GARFA','GEDIK','GEDZA','GENIL','GENTS','GEREL','GLYHO','GMTAS','GOKCE',
    'GOLTS','GOODY','GOZDE','GRNYO','GRSEL','GSDDE','GSDHO','GSRAY','GUBRF','GUSGR',
    'GUVEN','GVGYO','GWIND',
    'HATEK','HALKB','HALKS','HATSN','HEDEF','HEKTS','HLGYO','HMVEF','HOROZ','HRKET','HURGZ',
    'IEYHO','IGDAS','IHEVA','IHGZT','IHLGM','IHYAY','IMASM','INDES','INFO','INTEM',
    'IPEKE','IPGYO','ISGSY','ISGYO','ISKPL','ISYAT','ISCTR','ITTFK','IZFAS','IZKUR','IZOCM',
    'JANTS',
    'KAREL','KARSN','KARTN','KATMR','KAYSE','KBORU','KCAER','KCHOL','KENT','KEPEZ',
    'KERVT','KFEIN','KGYO','KLGYO','KLMSN','KNFRT','KONYA','KONTR','KOPOL','KORDS',
    'KOZA','KOZAA','KRDMA','KRDMB','KRDMD','KRTEK','KTLEV','KTSKR','KUTPO',
    'LIDER','LKMNH','LOGO',
    'MACKO','MAKIM','MAKTK','MANAS','MAPOL','MARTI','MAVI','MEDTR','MEGMT','MEKAG',
    'MEPA','MERCN','MERIT','MERKO','METRO','MGROS','MIELS','MMCAS','MNDRS','MOGAN',
    'MPARK','MSGYO','MTRKS','MTRYO',
    'NATEN','NETAS','NIBAS','NTGAZ','NTTUR','NUGYO','NUHCM',
    'ODAS','OFSYM','ONCSM','ONER','ORGE','ORMA','OSTIM','OTKAR','OTTO','OYLUM',
    'OZBAL','OZKGY','OZRDN','OZSUB',
    'PAGYO','PAPIL','PARSN','PEKGY','PENGD','PENTA','PETKM','PETUN','PGSUS','PINSU',
    'PKART','PKENT','PLTUR','PNSUT','POLHO','POLTK','PRDGS','PRPOL','PSDTC','PTOFS',
    'QNBFB','QNBFL',
    'RALYH','RAYSG','REDR','RGYAS','RODRG','ROYAL','RUBNS',
    'SAFKN','SAHOL','SAMAT','SANEL','SANFM','SANKO','SARKY','SASA','SAYAS','SDTTR',
    'SEKFK','SEKUR','SELEC','SELVA','SENTE','SILVR','SISE','SKBNK','SKTAS','SMART',
    'SNGYO','SNKRN','SODSN','SOKM','SRVGY','SUMAS','SUNUS','SURGY','SUWEN',
    'TABGD','TATGD','TAVHL','TCELL','TDGYO','TEKTU','TEZOL','THYAO','TKFEN','TKNSA',
    'TLMAN','TMPOL','TNZTP','TOASO','TRCAS','TRGYO','TRILC','TSGYO','TSKB','TSPOR',
    'TTKOM','TTRAK','TUCLK','TUKAS','TUMAS','TUPRS','TURGG','TURSG','TVORX','TYHOL',
    'ULKER','ULUSE','ULUUN','UNLU','URTEKS','USAK','USDMR',
    'VAKBN','VAKFN','VAKGM','VANGD','VBTYZ','VERUS','VESBE','VESTL','VKFYO','VKGYO',
    'YATAS','YATRM','YBTAS','YGYO','YIGIT','YKBNK','YKSLN','YONGA','YUNSA',
    'ZEDUR','ZOREN','ZRGYO'
  ];

  const HISSE_BATCH = 50;
  let hisseData = {};
  let hisseFilter_q = '';
  let sortCol = 'sym', sortAsc = true;
  let hisseCountdown = 60;
  let hisseCountdownTimer = null;
  let hisseLoadedBatches = 0, hisseTotalBatches = 0;
  let hisseInited = false;

  function fmt(n, d) {
    if (n == null || isNaN(n)) return '\u2013';
    return n.toLocaleString('tr-TR', { minimumFractionDigits: d, maximumFractionDigits: d });
  }
  function fmtVol(n) {
    if (!n) return '\u2013';
    if (n >= 1e9) return (n / 1e9).toFixed(2) + 'B';
    if (n >= 1e6) return (n / 1e6).toFixed(2) + 'M';
    if (n >= 1e3) return (n / 1e3).toFixed(1) + 'K';
    return n.toLocaleString('tr-TR');
  }
  function fmtTime(ts) {
    if (!ts) return '\u2013';
    return new Date(ts * 1000).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
  }

  function toggleSort(col) {
    if (sortCol === col) { sortAsc = !sortAsc; }
    else { sortCol = col; sortAsc = col === 'sym' || col === 'name'; }
    ['sym','name','price','chg','pct','vol'].forEach(c => {
      const el = document.getElementById('sort-' + c);
      if (!el) return;
      const labels = { sym:'SEMBOL', name:'\u015e\u0130RKET', price:'F\u0130YAT (\u20ba)', chg:'DE\u011e\u0130\u015e\u0130M', pct:'DE\u011e.%', vol:'HAC\u0130M' };
      el.textContent = c === sortCol ? labels[c] + (sortAsc ? ' \u2191' : ' \u2193') : labels[c];
    });
    hisseRenderTable();
  }

  function hisseFilter() {
    hisseFilter_q = (document.getElementById('hisse-search').value || '').toUpperCase().trim();
    hisseRenderTable();
  }

  function hisseRenderTable() {
    const tbody = document.getElementById('hisse-tbody');
    if (!tbody) return;
    let rows = Object.values(hisseData);
    if (hisseFilter_q) {
      rows = rows.filter(d => {
        const sym = (d.symbol || '').replace(/\.IS$/i, '');
        const name = (d.shortName || d.longName || '').toUpperCase();
        return sym.includes(hisseFilter_q) || name.includes(hisseFilter_q);
      });
    }
    rows.sort((a, b) => {
      let va, vb;
      const sa = (a.symbol || '').replace(/\.IS$/i, '');
      const sb = (b.symbol || '').replace(/\.IS$/i, '');
      if (sortCol === 'sym')   { va = sa; vb = sb; }
      else if (sortCol === 'name')  { va = (a.shortName || a.longName || sa).toUpperCase(); vb = (b.shortName || b.longName || sb).toUpperCase(); }
      else if (sortCol === 'price') { va = a.regularMarketPrice || 0; vb = b.regularMarketPrice || 0; }
      else if (sortCol === 'chg')   { va = a.regularMarketChange || 0; vb = b.regularMarketChange || 0; }
      else if (sortCol === 'pct')   { va = a.regularMarketChangePercent || 0; vb = b.regularMarketChangePercent || 0; }
      else if (sortCol === 'vol')   { va = a.regularMarketVolume || 0; vb = b.regularMarketVolume || 0; }
      if (va < vb) return sortAsc ? -1 : 1;
      if (va > vb) return sortAsc ? 1 : -1;
      return 0;
    });
    const count = document.getElementById('hisse-count');
    if (count) count.textContent = rows.length > 0 ? rows.length + ' hisse' : '';
    if (rows.length === 0) {
      const msg = Object.keys(hisseData).length === 0 ? 'Y\u00fckleniyor\u2026' : 'E\u015fle\u015fen hisse bulunamad\u0131.';
      tbody.innerHTML = '<tr><td colspan="8" class="mono" style="padding:48px 16px;text-align:center;color:#334155;font-size:13px">' + msg + '</td></tr>';
      return;
    }
    tbody.innerHTML = rows.map((d, i) => {
      const sym = (d.symbol || '').replace(/\.IS$/i, '');
      const company = d.shortName || d.longName || sym;
      const chg = d.regularMarketChange;
      const chgPct = d.regularMarketChangePercent;
      const isPos = chg > 0, isNeg = chg < 0;
      const cc = isPos ? 'pos' : isNeg ? 'neg' : 'neu';
      const arrow = isPos ? '\u25b2 ' : isNeg ? '\u25bc ' : '';
      const chgStr = (isPos ? '+' : '') + fmt(chg, 2);
      const chgPctStr = (isPos ? '+' : '') + fmt(chgPct, 2) + '%';
      const bg = i % 2 === 0 ? 'rgba(10,14,26,0.55)' : 'rgba(20,30,50,0.35)';
      const bgh = 'rgba(16,185,129,0.07)';
      return '<tr class="hisse-row" style="background:' + bg + '" onmouseover="this.style.background=\'' + bgh + '\'" onmouseout="this.style.background=\'' + bg + '\'">' +
        '<td class="hisse-td mono" style="text-align:center;font-size:11px;color:#334155">' + (i+1) + '</td>' +
        '<td class="hisse-td mono" style="font-weight:700;color:#6ee7b7;font-size:14px">' + sym + '</td>' +
        '<td class="hisse-td" style="color:#94a3b8;font-size:12px;max-width:200px;overflow:hidden;text-overflow:ellipsis" title="' + company + '">' + company + '</td>' +
        '<td class="hisse-td mono" style="text-align:right;font-weight:700;color:#e2e8f0;font-size:14px">' + fmt(d.regularMarketPrice, 2) + '</td>' +
        '<td class="hisse-td mono ' + cc + '" style="text-align:right;font-weight:600">' + arrow + chgStr + '</td>' +
        '<td class="hisse-td mono ' + cc + '" style="text-align:right;font-weight:700">' + chgPctStr + '</td>' +
        '<td class="hisse-td mono" style="text-align:right;color:#64748b;font-size:12px">' + fmtVol(d.regularMarketVolume) + '</td>' +
        '<td class="hisse-td mono" style="text-align:center;color:#475569;font-size:12px">' + fmtTime(d.regularMarketTime) + '</td>' +
        '</tr>';
    }).join('');
  }

  async function hisseFetchBatch(symbols) {
    const fields = 'regularMarketPrice,regularMarketChange,regularMarketChangePercent,regularMarketVolume,shortName,longName,regularMarketTime';
    const symsIS = symbols.map(s => s + '.IS').join(',');
    const base1 = 'https://query1.finance.yahoo.com/v8/finance/quote?symbols=' + encodeURIComponent(symsIS) + '&fields=' + fields + '&corsDomain=finance.yahoo.com';
    const base2 = 'https://query2.finance.yahoo.com/v8/finance/quote?symbols=' + encodeURIComponent(symsIS) + '&fields=' + fields + '&corsDomain=finance.yahoo.com';
    const attempts = [
      { url: base1, wrap: false },
      { url: 'https://corsproxy.io/?' + encodeURIComponent(base1), wrap: false },
      { url: 'https://api.allorigins.win/get?url=' + encodeURIComponent(base1), wrap: true },
      { url: 'https://corsproxy.io/?' + encodeURIComponent(base2), wrap: false },
      { url: 'https://api.allorigins.win/get?url=' + encodeURIComponent(base2), wrap: true }
    ];
    for (const a of attempts) {
      try {
        const r = await fetch(a.url, { headers: { 'Accept': 'application/json' } });
        if (!r.ok) continue;
        let json;
        if (a.wrap) { const w = await r.json(); json = JSON.parse(w.contents); }
        else json = await r.json();
        const quotes = json && json.quoteResponse && json.quoteResponse.result || [];
        if (quotes.length > 0) return quotes;
      } catch(e) {}
    }
    return [];
  }

  async function hisseFetchAll() {
    const btn = document.getElementById('hisse-refresh-btn');
    const icon = document.getElementById('hisse-refresh-icon');
    const status = document.getElementById('hisse-status');
    const pw = document.getElementById('hisse-progress-wrap');
    const pb = document.getElementById('hisse-progress-bar');
    if (btn) btn.disabled = true;
    if (icon) icon.classList.add('spinning');
    if (pw) pw.style.display = 'block';
    if (pb) pb.style.width = '0%';
    hisseData = {};
    hisseLoadedBatches = 0;
    const batches = [];
    for (let i = 0; i < BIST_ALL.length; i += HISSE_BATCH) batches.push(BIST_ALL.slice(i, i + HISSE_BATCH));
    hisseTotalBatches = batches.length;
    if (status) status.textContent = '0 / ' + BIST_ALL.length + ' arand\u0131...';
    await Promise.all(batches.map(async (batch) => {
      const quotes = await hisseFetchBatch(batch);
      quotes.forEach(q => {
        if (q && q.regularMarketPrice != null) {
          const sym = (q.symbol || '').replace(/\.IS$/i, '');
          hisseData[sym] = q;
        }
      });
      hisseLoadedBatches++;
      const done = Math.min(hisseLoadedBatches * HISSE_BATCH, BIST_ALL.length);
      if (status) status.textContent = done + ' / ' + BIST_ALL.length + ' arand\u0131...';
      if (pb) pb.style.width = Math.round((hisseLoadedBatches / hisseTotalBatches) * 100) + '%';
      hisseRenderTable();
    }));
    if (btn) btn.disabled = false;
    if (icon) icon.classList.remove('spinning');
    if (pb) { pb.style.width = '100%'; setTimeout(() => { if (pw) pw.style.display = 'none'; }, 600); }
    const now = new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const n = Object.keys(hisseData).length;
    if (status) status.textContent = 'son: ' + now + ' \u2014 ' + n + ' hisse';
    hisseRenderTable();
    hisseResetCountdown();
    lucide.createIcons();
  }

  function hisseResetCountdown() {
    hisseCountdown = 60;
    if (hisseCountdownTimer) clearInterval(hisseCountdownTimer);
    const el = document.getElementById('hisse-timer');
    if (el) el.textContent = hisseCountdown + 's';
    hisseCountdownTimer = setInterval(() => {
      hisseCountdown--;
      const el2 = document.getElementById('hisse-timer');
      if (el2) el2.textContent = hisseCountdown + 's';
      if (hisseCountdown <= 0) { clearInterval(hisseCountdownTimer); hisseFetchAll(); }
    }, 1000);
  }

  // HİSSE sayfasına geçince otomatik yükle
  function hisseOnActivate() {
    if (!hisseInited) { hisseInited = true; hisseFetchAll(); }
  }

"""
html = html.replace(LUCIDE_CALL, HISSE_JS + LUCIDE_CALL)
print('Hisse JS:', 'hisseFetchAll' in html)

# ── 5. Nav handler — trigger hisseOnActivate when hisse tab clicked ───────────
OLD_NAV_HANDLER = "      document.getElementById('kasa-header-actions').style.display = target === 'kasa' ? 'flex' : 'none';\n    });"
NEW_NAV_HANDLER = """      document.getElementById('kasa-header-actions').style.display = target === 'kasa' ? 'flex' : 'none';
      if (target === 'hisse') hisseOnActivate();
    });"""
html = html.replace(OLD_NAV_HANDLER, NEW_NAV_HANDLER)
print('Nav activate:', 'hisseOnActivate' in html)

with open(r'c:\Users\TheVaner\Desktop\KYO2.0\kyo20.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('DONE — written', len(html), 'chars to kyo20.html')
