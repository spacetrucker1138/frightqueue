(async()=>{
const res=await fetch('/data/games.json');const {games}=await res.json();
const label={demo:'Free demo',released:'Out now',upcoming:'Upcoming'};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const card=g=>`<article class="card"><a href="/games/${g.id}.html"><img src="${esc(g.image)}" alt="${esc(g.title)}" loading="lazy" width="460" height="215"></a>
<div class="b"><div><span class="pill ${g.status}">${label[g.status]}</span>${g.free?'<span class="pill free">Free</span>':''}<span class="pill">${esc(g.store)}</span></div>
<h3><a href="/games/${g.id}.html">${esc(g.title)}</a></h3><div class="meta">${esc(g.developer)} · ${esc(g.release_date)} · ${esc(g.platforms.join(', '))}</div>
<p class="blurb">${esc(g.blurb)}</p><div><a class="btn" href="${esc(g.link)}" rel="noopener sponsored" data-affiliate="${esc(g.store)}">${g.status==='demo'?'Play demo':'View'} on ${esc(g.store)}</a></div></div></article>`;
const now=new Date();const day=864e5;
const week=games.filter(g=>{const d=new Date(g.release_date);return !isNaN(d)&&/^\d{4}-\d\d-\d\d$/.test(g.release_date)&&Math.abs(d-now)<=7*day}).sort((a,b)=>a.release_date.localeCompare(b.release_date));
document.getElementById('week-grid').innerHTML=week.length?week.slice(0,8).map(card).join(''):'<p class="empty">Quiet week in the graveyard. Check the full Queue.</p>';
let f='all';const grid=document.getElementById('grid'),plat=document.getElementById('plat'),store=document.getElementById('store'),q=document.getElementById('q');
const order={upcoming:0,demo:1,released:2};
function render(){const t=q.value.toLowerCase();
const list=games.filter(g=>(f==='all'||(f==='free'?(g.free||g.status==='demo'):g.status===f))&&(!plat.value||g.platforms.includes(plat.value))&&(!store.value||g.store===store.value)&&(!t||[g.title,g.developer,...g.tags].join(' ').toLowerCase().includes(t)))
 .sort((a,b)=>order[a.status]-order[b.status]||(a.status==='upcoming'?a.release_date.localeCompare(b.release_date):b.release_date.localeCompare(a.release_date)));
grid.innerHTML=list.map(card).join('')||'<p class="empty">Nothing crawled out. Try another filter.</p>';
document.getElementById('count').textContent=`${list.length} game${list.length===1?'':'s'} in the queue`;}
document.querySelectorAll('.filters button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.filters button').forEach(x=>x.classList.remove('on'));b.classList.add('on');f=b.dataset.f;render();});
[plat,store].forEach(el=>el.onchange=render);q.oninput=render;render();
})();
