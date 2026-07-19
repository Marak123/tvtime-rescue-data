"""Generate a single self-contained HTML page to browse the recovered library.

The page has no external dependencies except the poster images, which load from
thetvdb.com (the same URLs TV Time itself used). Open it by double-clicking;
you need an internet connection the first time so the posters can load.
"""
from __future__ import annotations

import json
from pathlib import Path

_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TV Time - My library</title>
<style>
  :root{--bg:#0d1117;--bg2:#151b23;--card:#1b232d;--line:#273140;--txt:#e6edf3;
    --dim:#8b98a9;--accent:#f5c518;--green:#3fb950;--blue:#4493f8;--radius:12px}
  *{box-sizing:border-box}
  body{margin:0;background:linear-gradient(180deg,#0b0f14,#0d1117 320px);color:var(--txt);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
  a{color:var(--blue);text-decoration:none}
  header{padding:26px 20px 10px;max-width:1400px;margin:0 auto}
  .brand{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
  h1{font-size:25px;margin:0;font-weight:800}
  .who{color:var(--dim);font-size:14px}
  .stats{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0 4px}
  .stat{background:var(--bg2);border:1px solid var(--line);border-radius:999px;padding:7px 14px;font-size:13px}
  .stat b{color:var(--accent);font-size:15px}
  .controls{position:sticky;top:0;z-index:20;background:rgba(13,17,23,.86);backdrop-filter:blur(10px);
    border-bottom:1px solid var(--line);padding:12px 20px;margin-top:14px}
  .controls-inner{max-width:1400px;margin:0 auto;display:flex;gap:10px;flex-wrap:wrap;align-items:center}
  input,select{background:var(--card);border:1px solid var(--line);color:var(--txt);
    border-radius:9px;padding:9px 12px;font-size:14px;outline:none}
  input:focus,select:focus{border-color:var(--blue)}
  #q{flex:1;min-width:200px}
  .tabs{display:flex;gap:6px;flex-wrap:wrap}
  .tab{background:var(--card);border:1px solid var(--line);color:var(--dim);border-radius:999px;
    padding:8px 14px;font-size:13px;cursor:pointer;user-select:none}
  .tab.active{background:var(--accent);color:#111;border-color:var(--accent);font-weight:700}
  .epfilter{display:none;gap:6px}
  .epf{background:var(--card);border:1px solid var(--line);color:var(--dim);border-radius:999px;
    padding:7px 12px;font-size:12px;cursor:pointer;user-select:none}
  .epf.active{background:var(--green);color:#04210f;border-color:var(--green);font-weight:700}
  .count{color:var(--dim);font-size:13px;margin-left:auto}
  main{max-width:1400px;margin:0 auto;padding:18px 20px 60px}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:16px}
  .card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
    overflow:hidden;cursor:pointer;transition:transform .12s,border-color .12s;position:relative}
  .card:hover{transform:translateY(-4px);border-color:#3a4a5e}
  .poster{position:relative;aspect-ratio:2/3;background:#0f151c;overflow:hidden}
  .poster img{width:100%;height:100%;object-fit:cover;display:block}
  .poster .ph{position:absolute;inset:0;display:none;align-items:center;justify-content:center;
    padding:10px;text-align:center;font-size:13px;color:var(--dim);
    background:radial-gradient(circle at 50% 30%,#22303f,#131a22)}
  .poster.broken img{display:none}
  .poster.broken .ph{display:flex}
  .tag{position:absolute;top:8px;left:8px;font-size:11px;background:rgba(0,0,0,.72);
    border-radius:6px;padding:3px 7px;letter-spacing:.3px}
  .fav{position:absolute;top:8px;right:8px;font-size:13px}
  .done{position:absolute;bottom:8px;right:8px;background:var(--green);color:#04210f;border-radius:999px;
    width:23px;height:23px;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:800}
  .pbar{position:absolute;left:0;right:0;bottom:0;height:5px;background:rgba(0,0,0,.5)}
  .pbar i{display:block;height:100%;background:var(--green)}
  .meta{padding:9px 10px 11px}
  .title{font-size:13.5px;font-weight:600;line-height:1.25;
    display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:34px}
  .sub{color:var(--dim);font-size:12px;margin-top:4px}
  .empty{color:var(--dim);text-align:center;padding:60px 20px}
  .note{color:var(--dim);font-size:13px;line-height:1.5;background:var(--bg2);border:1px solid var(--line);
    border-radius:10px;padding:12px 14px;margin-bottom:16px}
  /* episode list */
  .epgroup{margin-bottom:18px;border:1px solid var(--line);border-radius:10px;overflow:hidden}
  .epshow{background:var(--bg2);padding:10px 14px;font-weight:700;font-size:14px;
    display:flex;justify-content:space-between;gap:10px;align-items:center}
  .epshow .n{color:var(--dim);font-weight:500;font-size:12px}
  .ep{display:flex;align-items:center;gap:12px;padding:9px 14px;border-top:1px solid var(--line);font-size:13.5px}
  .epcode{color:var(--dim);font-variant-numeric:tabular-nums;flex:none;width:64px}
  .eptitle{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .epstatus{flex:none;font-size:12px;color:var(--dim)}
  .epstatus.seen{color:var(--green);font-weight:600}
  .eprew{flex:none;font-size:11px;background:var(--accent);color:#111;border-radius:999px;padding:1px 7px;font-weight:700}
  .modal{position:fixed;inset:0;z-index:50;display:none;align-items:center;justify-content:center;padding:20px}
  .modal.open{display:flex}
  .backdrop{position:absolute;inset:0;background:rgba(0,0,0,.72)}
  .sheet{position:relative;max-width:820px;width:100%;max-height:88vh;overflow:auto;
    background:var(--bg2);border:1px solid var(--line);border-radius:16px}
  .hero{position:relative;height:220px;background:#0f151c}
  .hero img{width:100%;height:100%;object-fit:cover;opacity:.5}
  .hero::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,transparent,var(--bg2))}
  .sheet-body{padding:0 24px 26px;margin-top:-70px;position:relative;display:flex;gap:20px;flex-wrap:wrap}
  .sheet-poster{width:150px;flex:none;aspect-ratio:2/3;border-radius:10px;overflow:hidden;
    border:1px solid var(--line);background:#0f151c}
  .sheet-poster img{width:100%;height:100%;object-fit:cover}
  .sheet-info{flex:1;min-width:230px;padding-top:74px}
  .sheet-info h2{margin:0 0 6px;font-size:23px}
  .chips{display:flex;gap:7px;flex-wrap:wrap;margin:10px 0}
  .chip{background:var(--card);border:1px solid var(--line);border-radius:999px;padding:4px 11px;font-size:12px;color:var(--dim)}
  .chip.on{color:var(--txt)}
  .ov{color:#c9d4e0;line-height:1.55;margin-top:12px;font-size:14.5px}
  .kv{margin-top:14px;font-size:13.5px;color:var(--dim)}
  .kv b{color:var(--txt);font-weight:600}
  .modal-eps{margin-top:18px;border:1px solid var(--line);border-radius:10px;overflow:hidden}
  .modal-eps-h{background:var(--card);padding:9px 14px;font-weight:700;font-size:13px}
  .close{position:absolute;top:12px;right:14px;z-index:3;background:rgba(0,0,0,.6);border:none;
    color:#fff;font-size:20px;width:36px;height:36px;border-radius:50%;cursor:pointer}
  .footer{max-width:1400px;margin:0 auto;padding:0 20px 40px;color:var(--dim);font-size:12px}
</style>
</head>
<body>
<header>
  <div class="brand"><h1>TV Time - My library</h1><span class="who" id="who"></span></div>
  <div class="stats" id="stats"></div>
</header>
<div class="controls"><div class="controls-inner">
  <input id="q" type="search" placeholder="Search title, genre, year...">
  <div class="tabs" id="tabs"></div>
  <span class="epfilter" id="epfilter">
    <span class="epf active" data-ef="all">All</span>
    <span class="epf" data-ef="seen">Watched</span>
    <span class="epf" data-ef="unseen">Not watched</span>
  </span>
  <select id="sort">
    <option value="date">Recently watched</option>
    <option value="title">Title A-Z</option>
    <option value="year">Year (newest)</option>
    <option value="eps">Most episodes</option>
  </select>
  <span class="count" id="count"></span>
</div></div>
<main>
  <div class="grid" id="grid"></div>
  <div id="eplist" style="display:none"></div>
  <div class="empty" id="empty" style="display:none">No results.</div>
</main>
<div class="footer">Recovered locally from an iOS backup (DioCache.db). Posters from thetvdb.com. Private - for your eyes only.</div>
<div class="modal" id="modal">
  <div class="backdrop" data-close></div>
  <div class="sheet">
    <button class="close" data-close>&times;</button>
    <div class="hero"><img id="m-hero" alt=""></div>
    <div class="sheet-body">
      <div class="sheet-poster"><img id="m-poster" alt=""></div>
      <div class="sheet-info">
        <h2 id="m-title"></h2>
        <div class="chips" id="m-chips"></div>
        <div class="ov" id="m-ov"></div>
        <div class="kv" id="m-kv"></div>
        <div id="m-eps"></div>
      </div>
    </div>
  </div>
</div>
<script id="data" type="application/json">__TVDATA_JSON__</script>
<script>
const DATA = JSON.parse(document.getElementById('data').textContent);
const ALL = DATA.items; ALL.forEach((it,i)=>it._i=i);
const $ = s => document.querySelector(s);
function pad(n){return String(n||0).padStart(2,'0');}
function epCode(e){return 'S'+pad(e.season)+'E'+pad(e.number);}
function epStatus(e){return e.seen
  ? `<span class="epstatus seen">Watched${e.seen_date?' '+e.seen_date.slice(0,10):''}</span>`
  : `<span class="epstatus">Not watched</span>`;}
function epRew(e){return (e.times_watched||0)>1?`<span class="eprew">x${e.times_watched}</span>`:'';}

$('#who').textContent = DATA.profile.name ? ('account: ' + DATA.profile.name) : '';
const s = DATA.stats;
$('#stats').innerHTML = [['Movies',s.movies],['Series',s.series],
  ['Watched episodes',(s.episodes||0).toLocaleString('en')],
  ['Watchlist',s.watchlist],['Archived',s.archived]]
  .map(([l,v])=>`<span class="stat"><b>${v}</b> ${l}</span>`).join('');
const TABS=[['all','All'],['movie','Movies'],['series','Series'],
  ['watchlist','Watchlist'],['favorites','Favorites'],['archived','Archived'],['episodes','Episodes']];
let tab='all',sort='date',q='',epFilter='all';
$('#tabs').innerHTML = TABS.map(([k,l],i)=>`<span class="tab${i?'':' active'}" data-tab="${k}">${l}</span>`).join('');
$('#tabs').onclick=e=>{const t=e.target.closest('.tab');if(!t)return;
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
  t.classList.add('active');tab=t.dataset.tab;render();};
$('#epfilter').onclick=e=>{const t=e.target.closest('.epf');if(!t)return;
  document.querySelectorAll('.epf').forEach(x=>x.classList.remove('active'));
  t.classList.add('active');epFilter=t.dataset.ef;render();};
$('#q').oninput=e=>{q=e.target.value.trim().toLowerCase();render();};
$('#sort').onchange=e=>{sort=e.target.value;render();};

function matchTab(it){
  if(tab==='all')return true;
  if(tab==='movie')return it.kind==='movie';
  if(tab==='series')return it.kind==='series';
  if(tab==='watchlist')return it.watch_later||it.for_later;
  if(tab==='favorites')return it.favorite;
  if(tab==='archived')return it.archived;
  return true;}
function matchQ(it){if(!q)return true;
  return (it.title||'').toLowerCase().includes(q)||(it.year||'').includes(q)||
    (it.genres||[]).join(' ').toLowerCase().includes(q);}
function sorter(a,b){
  if(sort==='title')return (a.title||'').localeCompare(b.title||'');
  if(sort==='year')return (b.year||'').localeCompare(a.year||'');
  if(sort==='eps')return (b.watched_eps||0)-(a.watched_eps||0);
  return (b.sortDate||0)-(a.sortDate||0);}
function card(it){
  const broken=it.poster?'':' broken';
  const tag=it.kind==='movie'?'MOVIE':'SERIES';
  let done=(it.kind==='movie'&&it.watched)?'<div class="done">&#10003;</div>':'';
  let fav=it.favorite?'<div class="fav">&#9733;</div>':'';
  let pbar='';
  if(it.kind==='series'&&it.aired_eps){
    const pct=Math.min(100,Math.round(100*it.watched_eps/Math.max(it.aired_eps,it.watched_eps)));
    pbar=`<div class="pbar"><i style="width:${pct}%"></i></div>`;}
  let sub = it.kind==='movie'
    ? [it.year,it.watchedDate?('watched '+it.watchedDate):''].filter(Boolean).join(' - ')
    : `${it.watched_eps}/${it.aired_eps} eps - ${it.status==='Ended'?'Ended':'Running'}`;
  return `<div class="card" data-id="${it._i}"><div class="poster${broken}">
    ${it.poster?`<img loading="lazy" src="${it.poster}" onerror="this.parentElement.classList.add('broken')">`:''}
    <div class="ph">${it.title}</div><div class="tag">${tag}</div>${fav}${done}${pbar}</div>
    <div class="meta"><div class="title">${it.title}</div><div class="sub">${sub}</div></div></div>`;}

function renderEpisodes(){
  let eps=[];
  ALL.forEach(it=>{ if(it.kind==='series'&&it.episodes) it.episodes.forEach(e=>eps.push(e)); });
  eps=eps.filter(e=>{
    if(q && !((e.show||'').toLowerCase().includes(q)||(e.name||'').toLowerCase().includes(q))) return false;
    if(epFilter==='seen')return e.seen;
    if(epFilter==='unseen')return !e.seen;
    return true;});
  eps.sort((a,b)=>(a.show||'').localeCompare(b.show||'')||((a.season||0)-(b.season||0))||((a.number||0)-(b.number||0)));
  $('#count').textContent = eps.length+' episodes';
  let html='<div class="note">TV Time only saved these individual episodes (the ones around your '
    +'current progress). It kept the total watched and aired count for every series, but not the full '
    +'per-episode history, so this list is partial. The series cards still show your real totals.</div>';
  if(!eps.length){ html+='<div class="empty">No individual episodes match this filter.</div>'; $('#eplist').innerHTML=html; return; }
  let cur=null, buf='';
  eps.forEach(e=>{
    if(e.show!==cur){
      if(cur!==null) html+=buf+'</div>';
      cur=e.show;
      const total=eps.filter(x=>x.show===cur);
      const seen=total.filter(x=>x.seen).length;
      html+=`<div class="epgroup"><div class="epshow"><span>${e.show||'Unknown show'}</span>`
           +`<span class="n">${seen} watched / ${total.length} saved</span></div>`;
      buf='';
    }
    buf+=`<div class="ep"><span class="epcode">${epCode(e)}</span>`
        +`<span class="eptitle">${e.name||''}</span>${epRew(e)}${epStatus(e)}</div>`;
  });
  html+=buf+'</div>';
  $('#eplist').innerHTML=html;
}

function render(){
  const ep = tab==='episodes';
  $('#grid').style.display = ep?'none':'grid';
  $('#eplist').style.display = ep?'block':'none';
  $('#epfilter').style.display = ep?'flex':'none';
  $('#sort').style.display = ep?'none':'';
  $('#empty').style.display='none';
  if(ep){ renderEpisodes(); return; }
  const list=ALL.filter(it=>matchTab(it)&&matchQ(it)).sort(sorter);
  $('#count').textContent=list.length+' items';
  $('#grid').innerHTML=list.map(card).join('');
  $('#empty').style.display=list.length?'none':'block';
}
$('#grid').onclick=e=>{const c=e.target.closest('.card');if(c)openModal(ALL[+c.dataset.id]);};

function openModal(it){
  $('#m-title').textContent=it.title+(it.year?` (${it.year})`:'');
  $('#m-hero').src=it.fanart||it.poster||'';
  const mp=$('#m-poster');if(it.poster){mp.src=it.poster;mp.style.display='';}else mp.style.display='none';
  const chips=[`<span class="chip on">${it.kind==='movie'?'Movie':'Series'}</span>`];
  (it.genres||[]).forEach(g=>chips.push(`<span class="chip">${g}</span>`));
  if(it.kind==='series'){
    chips.push(`<span class="chip on">${it.status==='Ended'?'Ended':'Running'}</span>`);
    if(it.favorite)chips.push('<span class="chip on">Favorite</span>');
    if(it.archived)chips.push('<span class="chip">Archived</span>');
    if(it.for_later)chips.push('<span class="chip">Watchlist</span>');
  }else{
    if(it.watched)chips.push('<span class="chip on">Watched</span>');
    if(it.watch_later)chips.push('<span class="chip">Watchlist</span>');
    if(it.rewatch_count>0)chips.push(`<span class="chip">Rewatched x${it.rewatch_count}</span>`);}
  $('#m-chips').innerHTML=chips.join('');
  $('#m-ov').textContent=it.overview||(it.kind==='series'?'TV Time did not store series descriptions in the cache.':'No description.');
  const kv=[];
  if(it.kind==='series'){
    kv.push(`<b>Episodes:</b> ${it.watched_eps} watched of ${it.aired_eps} aired`);
    if(it.watchedDate)kv.push(`<b>Last watched:</b> ${it.watchedDate}`);
  }else{
    if(it.watchedDate)kv.push(`<b>Watched:</b> ${it.watchedDate}`);
    if(it.runtime_min)kv.push(`<b>Runtime:</b> ${it.runtime_min} min`);
    if(it.rating>0)kv.push(`<b>Your rating:</b> ${it.rating}/10`);
    if(it.imdb_id)kv.push(`<a href="https://www.imdb.com/title/${it.imdb_id}/" target="_blank" rel="noopener">IMDb</a>`);}
  $('#m-kv').innerHTML=kv.join(' &nbsp;-&nbsp; ');

  let epHtml='';
  if(it.kind==='series' && it.episodes && it.episodes.length){
    const list=it.episodes.slice().sort((a,b)=>((a.season||0)-(b.season||0))||((a.number||0)-(b.number||0)));
    const seen=list.filter(e=>e.seen).length;
    epHtml='<div class="modal-eps"><div class="modal-eps-h">Individual episodes saved in the backup ('
      +seen+' watched / '+list.length+' saved) - partial, only near your progress</div>';
    list.forEach(e=>{ epHtml+=`<div class="ep"><span class="epcode">${epCode(e)}</span>`
      +`<span class="eptitle">${e.name||''}</span>${epRew(e)}${epStatus(e)}</div>`; });
    epHtml+='</div>';
  }
  $('#m-eps').innerHTML=epHtml;
  $('#modal').classList.add('open');
}
document.querySelectorAll('[data-close]').forEach(x=>x.onclick=()=>$('#modal').classList.remove('open'));
document.addEventListener('keydown',e=>{if(e.key==='Escape')$('#modal').classList.remove('open')});
render();
</script>
</body>
</html>
"""


def build_site(lib: dict, out_html: Path) -> None:
    payload = {
        "items": lib["movies"] + lib["series"],
        "stats": lib["stats"],
        "profile": lib["profile"],
    }
    js = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    out_html.write_text(_TEMPLATE.replace("__TVDATA_JSON__", js), encoding="utf-8")
