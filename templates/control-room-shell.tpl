<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="description" content="BizTrust delivery control room generated from governed Markdown sources.">
  <meta name="theme-color" content="#071a2c">
  <meta name="generator" content="scripts/build_control_room.py">
  <meta name="source-digest" content="@@SOURCE_DIGEST@@">
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; img-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'">
  <title>Delivery Control Room · BizTrust</title>
  <style>
    :root {
      color-scheme: light;
      --navy-950: #061523;
      --navy-900: #071a2c;
      --navy-800: #102a43;
      --blue-700: #0f5ea8;
      --blue-600: #1673c7;
      --blue-100: #dceeff;
      --cyan-500: #17b6c7;
      --mint-500: #18a879;
      --amber-500: #ca7a00;
      --red-600: #bd2c3e;
      --paper: #f4f7fa;
      --surface: #ffffff;
      --surface-2: #edf3f7;
      --ink: #132536;
      --muted: #587083;
      --line: #d7e1e8;
      --shadow: 0 14px 36px rgba(6, 21, 35, .09);
      --radius: 14px;
      --font: Inter, "Noto Sans Lao", "Segoe UI", Arial, sans-serif;
    }
    [data-theme="dark"] {
      color-scheme: dark;
      --paper: #06121d;
      --surface: #0b2032;
      --surface-2: #112b40;
      --ink: #e8f1f6;
      --muted: #a6bac8;
      --line: #234057;
      --blue-100: #123f64;
      --shadow: 0 18px 42px rgba(0, 0, 0, .27);
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; scroll-padding-top: 8.5rem; }
    body {
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      font-family: var(--font);
      font-size: 1rem;
      line-height: 1.62;
    }
    a { color: var(--blue-700); text-underline-offset: .18em; }
    button, input { font: inherit; }
    button { cursor: pointer; }
    .cr-skip {
      position: fixed;
      z-index: 100;
      top: .75rem;
      left: .75rem;
      padding: .65rem 1rem;
      transform: translateY(-160%);
      background: var(--surface);
      border: 2px solid var(--blue-600);
      border-radius: .5rem;
    }
    .cr-skip:focus { transform: none; }
    .cr-topbar {
      position: sticky;
      z-index: 30;
      top: 0;
      min-height: 4.75rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      padding: .7rem clamp(1rem, 3vw, 2rem);
      color: #fff;
      background: rgba(7, 26, 44, .98);
      border-bottom: 1px solid rgba(255, 255, 255, .13);
    }
    .cr-brand {
      display: flex;
      align-items: center;
      gap: .85rem;
      color: #fff;
      text-decoration: none;
    }
    .cr-brand img {
      width: 8.3rem;
      max-height: 2.65rem;
      object-fit: contain;
      object-position: left center;
      filter: brightness(0) invert(1);
    }
    .cr-brand-copy { display: grid; line-height: 1.22; }
    .cr-brand-copy strong { font-size: .95rem; letter-spacing: .02em; }
    .cr-brand-copy small { color: #a9c5da; font-size: .76rem; }
    .cr-actions { display: flex; align-items: center; gap: .55rem; }
    .cr-actions a, .cr-actions button {
      min-height: 2.6rem;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: .55rem .85rem;
      color: #e9f5ff;
      background: transparent;
      border: 1px solid #38536a;
      border-radius: .55rem;
      text-decoration: none;
      font-size: .86rem;
      font-weight: 700;
    }
    .cr-actions a:hover, .cr-actions button:hover,
    .cr-actions a:focus-visible, .cr-actions button:focus-visible {
      background: #16374f;
      border-color: #69b9f5;
      outline: none;
    }
    .cr-shell {
      display: grid;
      grid-template-columns: 17rem minmax(0, 1fr);
      min-height: calc(100vh - 4.75rem);
    }
    .cr-sidebar {
      position: sticky;
      top: 4.75rem;
      align-self: start;
      height: calc(100vh - 4.75rem);
      overflow-y: auto;
      padding: 1.2rem .85rem 1.6rem;
      background: var(--surface);
      border-right: 1px solid var(--line);
    }
    .cr-nav-label {
      padding: .35rem .75rem .65rem;
      color: var(--muted);
      font-size: .75rem;
      font-weight: 800;
      letter-spacing: .12em;
      text-transform: uppercase;
    }
    .cr-sidebar nav { display: grid; gap: .22rem; }
    .cr-sidebar nav a {
      display: grid;
      grid-template-columns: 1.8rem minmax(0, 1fr);
      align-items: center;
      gap: 0 .42rem;
      padding: .58rem .66rem;
      color: var(--ink);
      border: 1px solid transparent;
      border-radius: .58rem;
      text-decoration: none;
    }
    .cr-sidebar nav a > span {
      grid-row: 1 / span 2;
      color: var(--blue-600);
      font-size: .72rem;
      font-weight: 800;
    }
    .cr-sidebar nav strong { overflow: hidden; text-overflow: ellipsis; font-size: .86rem; white-space: nowrap; }
    .cr-sidebar nav small { color: var(--muted); font-size: .68rem; }
    .cr-sidebar nav a:hover, .cr-sidebar nav a:focus-visible, .cr-sidebar nav a.is-active {
      background: var(--surface-2);
      border-color: var(--line);
      outline: none;
    }
    .cr-source-card {
      margin: 1rem .15rem 0;
      padding: .85rem;
      background: var(--navy-900);
      color: #e9f5ff;
      border-radius: .7rem;
    }
    .cr-source-card strong { display: block; font-size: .82rem; }
    .cr-source-card p { margin: .25rem 0 0; color: #a9c5da; font-size: .75rem; line-height: 1.45; }
    .cr-main { width: 100%; max-width: 100rem; min-width: 0; padding: clamp(1rem, 3vw, 2.2rem); }
    .cr-overview {
      position: relative;
      overflow: hidden;
      margin-bottom: 1rem;
      padding: clamp(1.1rem, 3vw, 1.8rem);
      background: var(--navy-900);
      color: #f3f8fb;
      border: 1px solid #183950;
      border-radius: var(--radius);
      box-shadow: var(--shadow);
    }
    .cr-overview::after {
      content: "";
      position: absolute;
      width: 24rem;
      height: 24rem;
      right: -11rem;
      top: -15rem;
      background: radial-gradient(circle, rgba(23, 182, 199, .2), transparent 66%);
      pointer-events: none;
    }
    .cr-overview-head {
      position: relative;
      z-index: 1;
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 1.5rem;
    }
    .cr-overview h1 { margin: .05rem 0 .35rem; font-size: clamp(1.55rem, 3vw, 2.35rem); line-height: 1.12; }
    .cr-overview-copy { max-width: 50rem; margin: 0; color: #afc6d6; }
    .cr-eyebrow {
      margin: 0 0 .35rem;
      color: var(--cyan-500);
      font-size: .75rem;
      font-weight: 800;
      letter-spacing: .12em;
      text-transform: uppercase;
    }
    .cr-freshness {
      flex: 0 0 auto;
      display: inline-flex;
      align-items: center;
      gap: .42rem;
      padding: .5rem .7rem;
      color: #d9f8ef;
      background: rgba(24, 168, 121, .14);
      border: 1px solid rgba(58, 216, 166, .4);
      border-radius: 999px;
      font-size: .78rem;
      font-weight: 800;
    }
    .cr-freshness::before { content: ""; width: .48rem; height: .48rem; background: #3ad8a6; border-radius: 50%; }
    .cr-freshness.is-stale { color: #ffe0ac; background: rgba(202, 122, 0, .14); border-color: rgba(244, 173, 61, .55); }
    .cr-freshness.is-stale::before { background: #f4ad3d; }
    .cr-stat-grid {
      position: relative;
      z-index: 1;
      display: grid;
      grid-template-columns: repeat(5, minmax(8rem, 1fr));
      gap: .65rem;
      margin-top: 1.2rem;
    }
    .cr-stat {
      min-width: 0;
      padding: .78rem;
      background: rgba(255, 255, 255, .055);
      border: 1px solid rgba(255, 255, 255, .12);
      border-radius: .68rem;
    }
    .cr-stat span { display: block; color: #9fb9ca; font-size: .71rem; font-weight: 700; text-transform: uppercase; }
    .cr-stat strong { display: block; margin-top: .24rem; overflow-wrap: anywhere; color: #fff; font-size: .88rem; line-height: 1.35; }
    .cr-primary-action {
      position: relative;
      z-index: 1;
      display: grid;
      grid-template-columns: auto minmax(0, 1fr) auto;
      align-items: center;
      gap: .8rem;
      margin-top: .75rem;
      padding: .8rem .9rem;
      background: #0e3652;
      border-left: 4px solid var(--cyan-500);
      border-radius: .52rem;
    }
    .cr-primary-action span { color: #7ee6ed; font-size: .72rem; font-weight: 800; letter-spacing: .08em; }
    .cr-primary-action strong { min-width: 0; font-size: .92rem; }
    .cr-primary-action button { padding: .44rem .7rem; color: #fff; background: transparent; border: 1px solid #4e7187; border-radius: .45rem; font-size: .76rem; }
    .cr-toolbar {
      position: sticky;
      z-index: 20;
      top: 4.75rem;
      display: flex;
      align-items: center;
      gap: .65rem;
      margin-bottom: 1rem;
      padding: .72rem;
      background: color-mix(in srgb, var(--paper) 88%, transparent);
      border: 1px solid var(--line);
      border-radius: .72rem;
      backdrop-filter: blur(12px);
    }
    .cr-search { position: relative; flex: 1 1 17rem; }
    .cr-search label { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
    .cr-search input {
      width: 100%;
      min-height: 2.7rem;
      padding: .55rem .8rem .55rem 2.35rem;
      color: var(--ink);
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: .56rem;
    }
    .cr-search::before { content: "⌕"; position: absolute; top: .42rem; left: .78rem; color: var(--muted); font-size: 1.2rem; }
    .cr-search input:focus { outline: 3px solid color-mix(in srgb, var(--blue-600) 24%, transparent); border-color: var(--blue-600); }
    .cr-filters { display: flex; gap: .35rem; overflow-x: auto; scrollbar-width: thin; }
    .cr-filter {
      flex: 0 0 auto;
      min-height: 2.45rem;
      padding: .45rem .7rem;
      color: var(--muted);
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 999px;
      font-size: .76rem;
      font-weight: 800;
    }
    .cr-filter[aria-pressed="true"] { color: #fff; background: var(--blue-700); border-color: var(--blue-700); }
    .cr-count { flex: 0 0 auto; min-width: 5rem; color: var(--muted); font-size: .76rem; text-align: right; }
    .cr-panel {
      margin-bottom: 1rem;
      padding: clamp(1rem, 2.5vw, 1.55rem);
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: 0 4px 16px rgba(6, 21, 35, .035);
    }
    .cr-panel[hidden] { display: none; }
    .cr-panel.is-stale { border-color: color-mix(in srgb, var(--amber-500) 65%, var(--line)); }
    .cr-panel.is-stale .cr-panel-head::after {
      content: "Snapshot stale — update Markdown";
      display: inline-flex;
      align-items: center;
      align-self: start;
      padding: .32rem .52rem;
      color: #7a4700;
      background: #fff1d6;
      border-radius: .4rem;
      font-size: .72rem;
      font-weight: 800;
    }
    [data-theme="dark"] .cr-panel.is-stale .cr-panel-head::after { color: #ffcf80; background: #513409; }
    .cr-panel-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; }
    .cr-panel h2 { margin: 0; font-size: clamp(1.32rem, 2vw, 1.7rem); line-height: 1.2; }
    .cr-summary-copy { max-width: 58rem; margin: .38rem 0 0; color: var(--muted); }
    .cr-source-links { flex: 0 0 auto; display: flex; gap: .42rem; }
    .cr-source-links a {
      padding: .38rem .55rem;
      border: 1px solid var(--line);
      border-radius: .45rem;
      text-decoration: none;
      font-size: .72rem;
      font-weight: 800;
    }
    .cr-meta { display: flex; flex-wrap: wrap; gap: .45rem; margin: .85rem 0 1rem; padding-bottom: .85rem; border-bottom: 1px solid var(--line); }
    .cr-meta > span { padding: .28rem .48rem; color: var(--muted); background: var(--surface-2); border-radius: .38rem; font-size: .73rem; font-weight: 700; }
    .cr-status { font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }
    .cr-status.is-positive { color: #08714e; background: #dcf7ec; }
    .cr-status.is-active { color: #0d5795; background: #dceeff; }
    .cr-status.is-warning { color: #865000; background: #fff0d1; }
    .cr-status.is-negative { color: #9b2032; background: #ffe4e8; }
    [data-theme="dark"] .cr-status.is-positive { color: #8ee8c9; background: #123f34; }
    [data-theme="dark"] .cr-status.is-active { color: #a8d8ff; background: #123f64; }
    [data-theme="dark"] .cr-status.is-warning { color: #ffd58d; background: #503509; }
    [data-theme="dark"] .cr-status.is-negative { color: #ffb7c0; background: #57232a; }
    .cr-markdown { max-width: 80rem; }
    .cr-markdown h3, .cr-markdown h4, .cr-markdown h5 { margin: 1.45rem 0 .55rem; line-height: 1.3; }
    .cr-markdown h3 { font-size: 1.1rem; }
    .cr-markdown h4 { color: var(--navy-800); font-size: .98rem; }
    [data-theme="dark"] .cr-markdown h4 { color: #c5dce9; }
    .cr-markdown p { margin: .55rem 0 .95rem; }
    .cr-markdown ul, .cr-markdown ol { margin: .55rem 0 1rem; padding-left: 1.35rem; }
    .cr-markdown li { margin: .34rem 0; }
    .cr-markdown code { padding: .12rem .3rem; color: #124f7d; background: var(--blue-100); border-radius: .3rem; font-size: .88em; }
    [data-theme="dark"] .cr-markdown code { color: #bfe3ff; }
    .cr-markdown pre { overflow-x: auto; padding: 1rem; color: #dceaf3; background: var(--navy-950); border-radius: .65rem; }
    .cr-markdown pre code { padding: 0; color: inherit; background: transparent; }
    .cr-markdown blockquote { margin: 1rem 0; padding: .75rem 1rem; background: var(--surface-2); border-left: 4px solid var(--cyan-500); border-radius: 0 .55rem .55rem 0; }
    .cr-markdown blockquote p { margin: 0; font-weight: 650; }
    .cr-task { display: flex; align-items: flex-start; gap: .42rem; list-style: none; margin-left: -1.35rem !important; }
    .cr-task input { width: 1rem; height: 1rem; margin-top: .25rem; accent-color: var(--mint-500); }
    .cr-table-wrap { overflow-x: auto; margin: .85rem 0 1.1rem; border: 1px solid var(--line); border-radius: .65rem; }
    .cr-table-wrap table { width: 100%; min-width: 42rem; border-collapse: collapse; font-size: .86rem; }
    .cr-table-wrap th, .cr-table-wrap td { padding: .68rem .75rem; vertical-align: top; border-bottom: 1px solid var(--line); text-align: left; }
    .cr-table-wrap th { color: var(--muted); background: var(--surface-2); font-size: .73rem; letter-spacing: .045em; text-transform: uppercase; }
    .cr-table-wrap tbody tr:last-child td { border-bottom: 0; }
    .cr-empty { padding: 2rem; color: var(--muted); background: var(--surface); border: 1px dashed var(--line); border-radius: var(--radius); text-align: center; }
    .cr-empty[hidden] { display: none; }
    .cr-footer { padding: 1.2rem 0 .2rem; color: var(--muted); font-size: .76rem; }
    .cr-footer code { overflow-wrap: anywhere; }
    :focus-visible { outline: 3px solid color-mix(in srgb, var(--blue-600) 55%, transparent); outline-offset: 2px; }
    @media (max-width: 76rem) {
      .cr-shell { grid-template-columns: 14.5rem minmax(0, 1fr); }
      .cr-stat-grid { grid-template-columns: repeat(3, 1fr); }
      .cr-toolbar { align-items: stretch; flex-wrap: wrap; }
      .cr-search { flex-basis: 100%; }
      .cr-filters { flex: 1; }
    }
    @media (max-width: 52rem) {
      html { scroll-padding-top: 9rem; }
      .cr-topbar { align-items: center; min-height: 4.2rem; }
      .cr-brand img { width: 6.7rem; }
      .cr-brand-copy small, .cr-actions .cr-print { display: none; }
      .cr-actions a, .cr-actions button { min-height: 2.45rem; padding: .45rem .6rem; font-size: .75rem; }
      .cr-shell { display: block; }
      .cr-sidebar {
        position: sticky;
        z-index: 25;
        top: 4.2rem;
        width: 100%;
        height: auto;
        padding: .45rem .75rem;
        overflow-x: auto;
        overflow-y: hidden;
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }
      .cr-nav-label, .cr-source-card { display: none; }
      .cr-sidebar nav { display: flex; width: max-content; }
      .cr-sidebar nav a { display: flex; gap: .38rem; padding: .5rem .65rem; }
      .cr-sidebar nav a > span { grid-row: auto; }
      .cr-sidebar nav small { display: none; }
      .cr-main { padding: .8rem; }
      .cr-overview-head { display: block; }
      .cr-freshness { margin-top: .8rem; }
      .cr-stat-grid { grid-template-columns: repeat(2, 1fr); }
      .cr-primary-action { grid-template-columns: 1fr auto; }
      .cr-primary-action span { grid-column: 1 / -1; }
      .cr-toolbar { top: 7.55rem; }
      .cr-count { display: none; }
      .cr-panel-head { display: block; }
      .cr-source-links { margin-top: .75rem; }
    }
    @media (max-width: 32rem) {
      .cr-brand-copy { display: none; }
      .cr-actions a { display: none; }
      .cr-stat-grid { grid-template-columns: 1fr; }
      .cr-primary-action { display: block; }
      .cr-primary-action strong { display: block; margin: .3rem 0 .65rem; }
      .cr-panel { padding: 1rem; }
      .cr-source-links { flex-wrap: wrap; }
    }
    @media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
    @media print {
      :root { --paper: #fff; --surface: #fff; --ink: #111; --muted: #444; --line: #bbb; }
      .cr-topbar, .cr-sidebar, .cr-toolbar, .cr-primary-action button, .cr-source-links { display: none !important; }
      .cr-shell { display: block; }
      .cr-main { max-width: none; padding: 0; }
      .cr-overview { color: #111; background: #fff; box-shadow: none; border: 2px solid #111; }
      .cr-overview-copy, .cr-stat span, .cr-stat strong { color: #111; }
      .cr-stat { border-color: #aaa; }
      .cr-panel { break-inside: avoid; box-shadow: none; }
      .cr-panel[hidden] { display: block; }
    }
  </style>
</head>
<body data-theme="light">
  <a class="cr-skip" href="#control-room-main">Skip to control room</a>
  <header class="cr-topbar">
    <a class="cr-brand" href="../index.html" aria-label="Return to BizTrust guide">
      <img src="../assets/unitrust-horizontal.png" alt="UniTrust Broker Insurance">
      <span class="cr-brand-copy"><strong>BizTrust Control Room</strong><small>Markdown-governed delivery status</small></span>
    </a>
    <div class="cr-actions">
      <a href="../index.html">Guide</a>
      <a href="https://github.com/bstBizEra/biztrust_guide/issues/32" target="_blank" rel="noopener noreferrer">Work Package ↗</a>
      <button id="themeToggle" type="button" aria-label="Toggle light and dark theme">Theme</button>
      <button class="cr-print" id="printControlRoom" type="button">Print</button>
    </div>
  </header>

  <div class="cr-shell">
    <aside class="cr-sidebar" aria-label="Control-room sections">
      <div class="cr-nav-label">Operational views</div>
      <nav id="controlRoomNav">@@NAVIGATION@@</nav>
      <div class="cr-source-card">
        <strong>Markdown is authoritative</strong>
        <p>@@SOURCE_COUNT@@ governed sections. HTML is reproducible display output, not a second ledger.</p>
      </div>
    </aside>

    <main class="cr-main" id="control-room-main">
      <section class="cr-overview" aria-labelledby="control-room-title" data-refresh-by="@@REFRESH_BY@@">
        <div class="cr-overview-head">
          <div>
            <p class="cr-eyebrow">Delivery intelligence · source-controlled</p>
            <h1 id="control-room-title">Delivery Control Room</h1>
            <p class="cr-overview-copy">The current execution picture, generated from governed Markdown. Change the source, regenerate, review the diff, and bind evidence to the resulting revision.</p>
          </div>
          <div class="cr-freshness" id="freshnessBadge">
            <span>Snapshot current</span>
          </div>
        </div>

        <div class="cr-stat-grid" aria-label="Executive delivery snapshot">
          <article class="cr-stat"><span>Work Package</span><strong>@@WORK_PACKAGE@@</strong></article>
          <article class="cr-stat"><span>Delivery state</span><strong class="@@DELIVERY_STATUS_CLASS@@">@@DELIVERY_STATUS@@</strong></article>
          <article class="cr-stat"><span>Architecture gate</span><strong>@@ARCHITECTURE_STATE@@</strong></article>
          <article class="cr-stat"><span>Active slice</span><strong>@@ACTIVE_SLICE@@</strong></article>
          <article class="cr-stat"><span>Evidence</span><strong>@@EVIDENCE@@</strong></article>
        </div>

        <div class="cr-primary-action">
          <span>ONE PRIMARY NEXT ACTION</span>
          <strong id="primaryAction">@@PRIMARY_ACTION@@</strong>
          <button id="copyPrimaryAction" type="button">Copy action</button>
        </div>
      </section>

      <div class="cr-toolbar" aria-label="Control-room filters">
        <div class="cr-search">
          <label for="controlRoomSearch">Search control-room sections</label>
          <input id="controlRoomSearch" type="search" placeholder="Search action, owner, risk, evidence…" autocomplete="off">
        </div>
        <div class="cr-filters" role="group" aria-label="Filter sections by function">
          <button class="cr-filter" type="button" data-kind="all" aria-pressed="true">All</button>
          <button class="cr-filter" type="button" data-kind="execution" aria-pressed="false">Execution</button>
          <button class="cr-filter" type="button" data-kind="planning" aria-pressed="false">Planning</button>
          <button class="cr-filter" type="button" data-kind="governance" aria-pressed="false">Governance</button>
          <button class="cr-filter" type="button" data-kind="assurance" aria-pressed="false">Assurance</button>
          <button class="cr-filter" type="button" data-kind="continuity" aria-pressed="false">Handoff</button>
          <button class="cr-filter" type="button" data-kind="research" aria-pressed="false">Research</button>
        </div>
        <output class="cr-count" id="visibleCount" aria-live="polite">@@SOURCE_COUNT@@ sections</output>
      </div>

      <div id="controlRoomPanels">@@PANELS@@</div>
      <p class="cr-empty" id="controlRoomEmpty" hidden>No sections match this filter. Clear the search or select All.</p>

      <footer class="cr-footer">
        <p>Generated from @@SOURCE_COUNT@@ Markdown sources · updated @@UPDATED@@ · snapshot <time id="snapshotTime" datetime="@@SNAPSHOT_AT@@">@@SNAPSHOT_AT@@</time></p>
        <p>Source digest <code>@@SOURCE_DIGEST@@</code></p>
      </footer>
    </main>
  </div>

  <script id="controlRoomData" type="application/json">@@PAGE_DATA@@</script>
  <script>
    (() => {
      'use strict';
      const root = document.documentElement;
      const body = document.body;
      const panels = [...document.querySelectorAll('.cr-panel')];
      const filters = [...document.querySelectorAll('.cr-filter')];
      const search = document.getElementById('controlRoomSearch');
      const count = document.getElementById('visibleCount');
      const empty = document.getElementById('controlRoomEmpty');
      const freshness = document.getElementById('freshnessBadge');
      const theme = document.getElementById('themeToggle');
      const printButton = document.getElementById('printControlRoom');
      const copyButton = document.getElementById('copyPrimaryAction');
      const primaryAction = document.getElementById('primaryAction');
      let activeKind = 'all';

      try {
        const savedTheme = localStorage.getItem('biztrust-control-room-theme');
        const darkPreferred = window.matchMedia('(prefers-color-scheme: dark)').matches;
        body.dataset.theme = savedTheme || (darkPreferred ? 'dark' : 'light');
      } catch (_) {
        body.dataset.theme = 'light';
      }

      function applyFilters() {
        const query = (search.value || '').trim().toLocaleLowerCase();
        let visible = 0;
        panels.forEach((panel) => {
          const matchesKind = activeKind === 'all' || panel.dataset.kind === activeKind;
          const matchesQuery = !query || panel.textContent.toLocaleLowerCase().includes(query);
          panel.hidden = !(matchesKind && matchesQuery);
          if (!panel.hidden) visible += 1;
        });
        count.textContent = visible + (visible === 1 ? ' section' : ' sections');
        empty.hidden = visible !== 0;
      }

      filters.forEach((button) => button.addEventListener('click', () => {
        activeKind = button.dataset.kind;
        filters.forEach((item) => item.setAttribute('aria-pressed', String(item === button)));
        applyFilters();
      }));
      search.addEventListener('input', applyFilters);
      window.addEventListener('keydown', (event) => {
        if (event.key === '/' && document.activeElement !== search) {
          event.preventDefault();
          search.focus();
        }
      });

      function markFreshness(element) {
        const value = element.dataset.refreshBy;
        if (!value) return false;
        const stale = Date.now() >= Date.parse(value);
        element.classList.toggle('is-stale', stale);
        return stale;
      }
      const overview = document.querySelector('.cr-overview');
      const overviewStale = markFreshness(overview);
      panels.forEach(markFreshness);
      const refreshBy = overview.dataset.refreshBy;
      freshness.classList.toggle('is-stale', overviewStale);
      freshness.querySelector('span').textContent = overviewStale
        ? 'Snapshot stale — refresh source'
        : 'Current until ' + new Intl.DateTimeFormat(undefined, {dateStyle: 'medium', timeStyle: 'short'}).format(new Date(refreshBy));

      theme.addEventListener('click', () => {
        const next = body.dataset.theme === 'dark' ? 'light' : 'dark';
        body.dataset.theme = next;
        try { localStorage.setItem('biztrust-control-room-theme', next); } catch (_) {}
      });
      printButton.addEventListener('click', () => window.print());
      copyButton.addEventListener('click', async () => {
        const original = copyButton.textContent;
        try {
          await navigator.clipboard.writeText(primaryAction.textContent.trim());
          copyButton.textContent = 'Copied';
        } catch (_) {
          copyButton.textContent = 'Copy unavailable';
        }
        window.setTimeout(() => { copyButton.textContent = original; }, 1500);
      });

      if ('IntersectionObserver' in window) {
        const navLinks = [...document.querySelectorAll('#controlRoomNav a')];
        const observer = new IntersectionObserver((entries) => {
          entries.forEach((entry) => {
            if (!entry.isIntersecting) return;
            navLinks.forEach((link) => link.classList.toggle('is-active', link.hash === '#' + entry.target.id));
          });
        }, {rootMargin: '-22% 0px -68% 0px'});
        panels.forEach((panel) => observer.observe(panel));
      }

      root.dataset.controlRoomReady = 'true';
    })();
  </script>
</body>
</html>
