const CFG=window.APP_CONFIG;document.title=CFG.name;appname.textContent=CFG.name;tagline.textContent=CFG.tagline;
const $=s=>document.querySelector(s);const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let VIDS=[],SERIES=[],ARTS=[],PODS=[],HIDE=new Set();
const J=u=>fetch(u).then(r=>r.ok?r.json():null).catch(()=>null);
const clean=t=>String(t).replace(/#\S+/g,'').trim();
const vcard=v=>`<a class="vcard" href="${v.url}" target="_blank" rel="noopener"><img loading="lazy" src="${v.thumbnail}" alt=""><span>${esc(clean(v.title))}</span><small>${(v.published||'').slice(0,10)}${v.type==='short'?'・Shorts':''}</small></a>`;
const kindLabel={md:'文章',pdf:'PDF',slides:'簡報',link:'連結',file:'檔案'};
const acard=a=>`<div class="card acard" data-art="${esc(a.id)}">${a.thumb?`<img src="${a.thumb}" alt="" loading="lazy">`:''}<div><div class="ameta"><b class="badge">${kindLabel[a.kind]||'文章'}</b> ${esc(a.date)}</div><div class="atitle">${esc(a.title)}</div><div class="asum">${esc(a.summary)}</div><div class="chips">${(a.tags||[]).map(x=>`<span class="tag">#${esc(x)}</span>`).join('')}</div></div></div>`;
const pcard=p=>`<div class="card acard" data-pod="${esc(p.id)}"><div><div class="ameta"><b class="badge">Podcast</b> ${esc(p.date)}${p.audio?'・音檔':p.embed?'・外部平台':''}</div><div class="atitle">${esc(p.title)}</div><div class="asum">${esc(p.summary)}</div></div></div>`;
function seriesList(){/* 播放清單優先；沒有時用標題規則「｜系列名 EPxx」 */
 const byId=Object.fromEntries(VIDS.map(v=>[v.id,v]));let S=SERIES.map(s=>({name:s.title,url:s.url,vids:s.videos.map(i=>byId[i]).filter(Boolean)})).filter(s=>s.vids.length);
 if(!S.length){const m={};VIDS.forEach(v=>{const r=v.title.match(/｜\s*([^｜]+?)\s*(?:EP\s*\d+|（[上中下]）)/);if(r)(m[r[1]]=m[r[1]]||[]).push(v)});S=Object.entries(m).map(([name,vids])=>({name,vids}))}
 const longN=x=>x.vids.filter(v=>v.type!=='short').length;return S.sort((a,b)=>longN(b)-longN(a)||b.vids.length-a.vids.length)}
function feat(){return (CFG.featured||[]).map(f=>{const s=seriesList().find(x=>x.name.includes(f.match));const vids=s?s.vids:VIDS.filter(v=>v.title.includes(f.match));return{...f,vids,url:s&&s.url}}).filter(f=>f.vids.length)}
function footer(){return `<footer>${CFG.about?`<p>${esc(CFG.about)}</p>`:''}<p><a href="${CFG.channel}" target="_blank" rel="noopener">YouTube 頻道</a>${CFG.sister?`　｜　姊妹站：<a href="${CFG.sister.url}" target="_blank" rel="noopener">${esc(CFG.sister.name)}</a>（${esc(CFG.sister.desc)}）`:''}</p></footer>`}
function renderHome(){const latest=[...ARTS.map(a=>({...a,_k:'a'})),...PODS.map(p=>({...p,_k:'p'}))].sort((a,b)=>b.date.localeCompare(a.date)).slice(0,4);
view.innerHTML=`<div class="card hero"><p>${esc(CFG.about)}</p></div>
<h2>最新影片</h2><div class="vrow">${VIDS.slice(0,6).map(vcard).join('')}</div>
<h2>精選系列</h2>${feat().map((f,i)=>`<div class="card series" data-series="${esc(f.name)}"><div class="st">♟ ${esc(f.name)}</div><small>${f.vids.length} 支影片</small><p class="asum">${esc(f.desc||'')}</p><div class="vrow">${f.vids.slice(0,4).map(vcard).join('')}</div></div>`).join('')}
<h2>最新文章與 Podcast</h2>${latest.length?latest.map(x=>x._k==='a'?acard(x):pcard(x)).join(''):'<p class="empty">還沒有內容。</p>'}${footer()}`}
let VF='series';
function renderVideos(f,focus){VF=f||VF;const S=seriesList();const inS=new Set(S.flatMap(s=>s.vids.map(v=>v.id)));
const tabs=[['series','依系列'],['all','全部'],['video','長片'],['short','Shorts']];
let body='';if(VF==='series'){body=S.map(s=>`<div class="card" id="s-${esc(s.name)}"><h3>♟ ${esc(s.name)}（${s.vids.length}）</h3><div class="vrow">${s.vids.map(vcard).join('')}</div>${s.url?`<a class="tag" href="${s.url}" target="_blank" rel="noopener">在 YouTube 開啟播放清單 ›</a>`:''}</div>`).join('');
 const other=VIDS.filter(v=>!inS.has(v.id));if(other.length)body+=`<div class="card"><h3>其他影片（${other.length}）</h3><div class="vrow">${other.map(vcard).join('')}</div></div>`}
else body=`<div class="vgrid">${VIDS.filter(v=>VF==='all'||v.type===VF).map(vcard).join('')}</div>`;
view.innerHTML=`<h2>全部影片（${VIDS.length}）</h2><div class="chips">${tabs.map(([k,n])=>`<button class="chip ${k===VF?'sel':''}" data-vf="${k}">${n}</button>`).join('')}</div>${body}${footer()}`;
document.querySelectorAll('[data-vf]').forEach(b=>b.onclick=()=>renderVideos(b.dataset.vf));
if(focus){const el=document.getElementById('s-'+focus);if(el)el.scrollIntoView({block:'start'})}}
function renderArticles(t){const tags=[...new Set(ARTS.flatMap(a=>a.tags||[]))];const L=ARTS.filter(a=>!t||(a.tags||[]).includes(t));
view.innerHTML=`<h2>文章與簡報</h2>${tags.length>1?`<div class="chips"><button class="chip ${!t?'sel':''}" data-at="">全部</button>${tags.map(x=>`<button class="chip ${x===t?'sel':''}" data-at="${esc(x)}">${esc(x)}</button>`).join('')}</div>`:''}${L.length?L.map(acard).join(''):'<p class="empty">還沒有文章。</p>'}${footer()}`;
document.querySelectorAll('[data-at]').forEach(b=>b.onclick=()=>renderArticles(b.dataset.at))}
async function mdInto(el,path){try{let t=await fetch(path).then(r=>{if(!r.ok)throw 0;return r.text()});t=t.replace(/^---\s*\n[\s\S]*?\n---\s*\n?/,'');el.innerHTML=marked.parse(t);const base=path.replace(/[^/]+$/,'');
el.querySelectorAll('img').forEach(i=>{const s=i.getAttribute('src');if(s&&!/^(https?:|data:|\/)/.test(s))i.src=base+s});el.querySelectorAll('a[href^="http"]').forEach(x=>{x.target='_blank';x.rel='noopener'});el.querySelectorAll('script,iframe,object').forEach(x=>x.remove())}catch(e){el.textContent='載入失敗（離線時需先開啟過一次）。'}}
function renderArticle(id){const a=ARTS.find(x=>x.id===id);if(!a)return renderArticles();const v=a.video&&VIDS.find(x=>x.id===a.video);
view.innerHTML=`<button class="chip back" data-v="articles">‹ 文章列表</button><article class="card art"><div class="ameta"><b class="badge">${kindLabel[a.kind]||'文章'}</b> ${esc(a.date)}</div><h2>${esc(a.title)}</h2><div class="chips">${(a.tags||[]).map(x=>`<span class="tag">#${esc(x)}</span>`).join('')}</div>
<div id="artbody">${a.md?'載入中…':`<p>${esc(a.summary)}</p>`}</div>${a.embed?`<div class="embed"><iframe src="${a.embed}" allowfullscreen loading="lazy"></iframe></div>`:''}
${a.pdf&&!a.md&&a.thumb?`<a href="${a.pdf}" target="_blank" rel="noopener"><img style="width:100%;border-radius:8px" src="${a.thumb}" alt="PDF 第一頁"></a>`:''}
<div>${a.pdf?`<a class="btn" href="${a.pdf}" target="_blank" rel="noopener">開啟 PDF</a><a class="btn ghost" href="${a.pdf}" download>下載 PDF</a>`:''}${a.pptx?`<a class="btn ghost" href="${a.pptx}" download>下載 PPTX</a>`:''}${a.docx?`<a class="btn ghost" href="${a.docx}" download>下載 Word</a>`:''}${a.link?`<a class="btn ghost" href="${esc(a.link)}" target="_blank" rel="noopener">開啟原始連結</a>`:''}</div></article>
${v?`<div class="card"><h3>相關影片</h3><div class="vrow">${vcard(v)}</div></div>`:''}${footer()}`;if(a.md)mdInto($('#artbody'),a.md)}
const fmtT=s=>{s=Math.floor(s);const h=Math.floor(s/3600),m=Math.floor(s%3600/60),x=s%60;return(h?h+':':'')+String(m).padStart(h?2:1,'0')+':'+String(x).padStart(2,'0')};
function renderPodcast(){view.innerHTML=`<h2>Podcast</h2>${(CFG.podcastLinks||[]).length?`<div class="chips">${CFG.podcastLinks.map(l=>`<a class="chip" href="${l.url}" target="_blank" rel="noopener">${esc(l.label)}</a>`).join('')}</div>`:''}
${PODS.length?PODS.map(pcard).join(''):'<p class="empty">還沒有節目。把音檔（mp3/m4a）或含 Spotify／Apple Podcasts 連結的 .txt 上傳到 content/inbox 就會出現在這裡。</p>'}${footer()}`}
function renderEpisode(id){const p=PODS.find(x=>x.id===id);if(!p)return renderPodcast();
view.innerHTML=`<button class="chip back" data-v="podcast">‹ 節目列表</button><article class="card art"><div class="ameta"><b class="badge">Podcast</b> ${esc(p.date)}</div><h2>${esc(p.title)}</h2>
${p.audio?`<audio id="player" controls preload="metadata" src="${p.audio}"></audio>`:''}${p.embed?`<div class="embed ${/spotify|apple|soundcloud/.test(p.embed)?'audio':''}"><iframe src="${p.embed}" allow="autoplay; encrypted-media" loading="lazy"></iframe></div>`:''}
${p.chapters&&p.chapters.length?`<h3>章節</h3>${p.chapters.map(c=>`<div class="chap" data-t="${c.t}"><b>${fmtT(c.t)}</b><span>${esc(c.title)}</span></div>`).join('')}`:''}
<div id="artbody">${p.notes?'載入中…':`<p>${esc(p.summary)}</p>`}</div>
<div>${p.audio?`<a class="btn ghost" href="${p.audio}" download>下載音檔</a>`:''}${p.link?`<a class="btn ghost" href="${esc(p.link)}" target="_blank" rel="noopener">在原平台收聽</a>`:''}</div></article>${footer()}`;
document.querySelectorAll('.chap').forEach(c=>c.onclick=()=>{const a=$('#player');if(a){a.currentTime=+c.dataset.t;a.play()}});
if(p.notes)mdInto($('#artbody'),p.notes).then(()=>{if(p.chapters&&p.chapters.length)$('#artbody').querySelectorAll('li,p').forEach(e=>{if(/^\s*(\d{1,2}:)?\d{1,2}:\d{2}\s/.test(e.textContent))e.remove()})})}
function go(v,arg){document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('on',b.dataset.v===({article:'articles',episode:'podcast'}[v]||v)));
const R={home:renderHome,videos:renderVideos,articles:renderArticles,article:renderArticle,podcast:renderPodcast,episode:renderEpisode};(R[v]||renderHome)(arg);
history.replaceState(0,'','#'+v+(arg?'/'+encodeURIComponent(arg):''));scrollTo(0,0)}
function route(){const h=location.hash.slice(1).split('/');go(h[0]||'home',h[1]?decodeURIComponent(h[1]):undefined)}
document.addEventListener('click',e=>{const t=e.target.closest('[data-v],[data-art],[data-pod],[data-series]');if(!t)return;
if(t.dataset.art)go('article',t.dataset.art);else if(t.dataset.pod)go('episode',t.dataset.pod);else if(t.dataset.series&&!e.target.closest('a')){go('videos');renderVideos('series',t.dataset.series)}else if(t.dataset.v)go(t.dataset.v)});
window.addEventListener('hashchange',route);
Promise.all([J('data/videos.json'),J('data/series.json'),J('data/articles.json'),J('data/podcast.json'),J('data/podcast_feed.json'),J('data/overrides.json')]).then(([v,s,a,p,pf,ov])=>{
ov=ov||{};HIDE=new Set(Object.keys(ov).filter(k=>ov[k]&&ov[k].hide));VIDS=((v&&v.videos)||[]).filter(x=>!HIDE.has(x.id)&&x.published).sort((a,b)=>b.published.localeCompare(a.published));
SERIES=s||[];ARTS=a||[];PODS=[...(p||[]),...(pf||[])].sort((x,y)=>(y.date||'').localeCompare(x.date||''));route()});
if('serviceWorker' in navigator)navigator.serviceWorker.register('sw.js');
