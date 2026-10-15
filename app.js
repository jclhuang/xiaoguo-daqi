const CFG=window.APP_CONFIG;document.title=CFG.name;appname.textContent=CFG.name;tagline.textContent=CFG.tagline;
let V=[],PL={},POSTS=[],UPD='';const $=s=>document.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const TOPICS=['全部','兩岸關係','中美關係','台灣','新加坡','地緣政治','其他'];
const thumb=id=>`https://i.ytimg.com/vi/${id}/hqdefault.jpg`, yt=id=>`https://youtu.be/${id}`;
const subUrl=CFG.channel+'?sub_confirmation=1';
const fmtD=s=>{const d=new Date(s);return `${d.getFullYear()}/${d.getMonth()+1}/${d.getDate()}`};
const clean=t=>String(t).replace(/\s#\S+/g,'').replace(/^\|/,'').trim();
function toast(t){const e=$('#toast');e.textContent=t;e.classList.add('on');setTimeout(()=>e.classList.remove('on'),1800)}
const longs=()=>V.filter(v=>!v.short), shorts=()=>V.filter(v=>v.short);
const CN={'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10};
function epOf(t){let m=t.match(/EP\s*0?(\d+)/i)||t.match(/第([一二三四五六七八九十\d]+)集/);if(!m)return null;let n=isNaN(m[1])?CN[m[1]]:+m[1];
 const p=(t.match(/（([上中下])）/)||[])[1];return {n,p,k:n*10+({上:1,中:2,下:3}[p]||0)}}
function seriesEps(s){return longs().filter(v=>v.title.includes(s.match)).map(v=>({...v,ep:epOf(v.title)})).sort((a,b)=>(a.ep?.k??999)-(b.ep?.k??999)||a.published.localeCompare(b.published))}
const vcard=v=>`<div class="v" data-id="${v.id}"><img loading="lazy" src="${thumb(v.id)}" alt=""><div class="t">${esc(clean(v.title))}</div><div class="m">${fmtD(v.published)}${v.topics?' ・ '+v.topics.filter(x=>x!=='其他').join('・'):''}</div></div>`;
function home(){const L=longs(),latest=L[0],feat=V.filter(v=>v.featured&&v.id!==latest?.id);
 view.innerHTML=(latest?`<h2>最新一集</h2><div class="hero v" data-id="${latest.id}"><img src="https://i.ytimg.com/vi/${latest.id}/maxresdefault.jpg" onerror="this.src='${thumb(latest.id)}'" alt=""><div class="play">▶</div><div class="cap"><span class="badge">NEW</span><span class="m">${fmtD(latest.published)}</span><div class="t">${esc(clean(latest.title))}</div></div></div>`:'')
 +`<div class="card sub"><img src="icons/icon-192.png" alt=""><div style="flex:1"><b>每週一集深度解析</b><div class="m" style="font-size:13px;color:var(--mute)">訂閱頻道，新片上線第一時間收到通知</div></div><a class="btn" href="${subUrl}" target="_blank" rel="noopener">訂閱</a></div>`
 +(feat.length?`<h2>精選推薦</h2><div class="row">${feat.map(vcard).join('')}</div>`:'')
 +CFG.series.map(s=>{const e=seriesEps(s);return `<h2>專題｜${esc(s.name)}</h2><div class="row">${e.map(vcard).join('')}</div>`}).join('')
 +`<h2>近期影片</h2><div class="row">${L.slice(1,9).map(vcard).join('')}</div>`
 +(shorts().length?`<h2>短影音</h2><div class="row">${shorts().slice(0,10).map(vcard).join('')}</div>`:'')
 +(POSTS[0]?`<h2>最新簡報／文章</h2>${postCard(POSTS[0])}`:'')+`<div class="upd">影片資料更新：${UPD?new Date(UPD).toLocaleString('zh-TW'):'—'}</div>`}
let curT='全部',q='',showShorts=false;
function videos(){view.innerHTML=`<input type="search" id="q" placeholder="搜尋影片標題…" value="${esc(q)}"><div class="chips" id="tp">${TOPICS.map(t=>`<button class="chip ${t===curT?'on':''}" data-t="${t}">${t}</button>`).join('')}<button class="chip ${showShorts?'on':''}" id="sh">含短影音</button></div><div class="grid" id="vg"></div>`;
 const draw=()=>{const qq=q.trim().toLowerCase();const r=V.filter(v=>(showShorts||!v.short)&&(curT==='全部'||v.topics?.includes(curT))&&(!qq||v.title.toLowerCase().includes(qq)||(v.desc||'').toLowerCase().includes(qq)));
  $('#vg').innerHTML=r.length?r.map(vcard).join(''):'<div class="empty" style="grid-column:1/-1">找不到符合的影片</div>'};
 $('#q').oninput=e=>{q=e.target.value;draw()};$('#tp').onclick=e=>{const b=e.target.closest('button');if(!b)return;if(b.id==='sh')showShorts=!showShorts;else curT=b.dataset.t;videos()};draw()}
function series(){view.innerHTML=CFG.series.map(s=>{const e=seriesEps(s);return `<div class="card series"><div class="sn">${esc(s.name)}</div><p>${esc(s.desc)}</p><p style="color:var(--mute);font-size:12px">共 ${e.length} 集・依集數排序</p>
 ${e.map(v=>`<div class="ep" data-id="${v.id}"><div class="no">${v.ep?`EP<b>${v.ep.n}</b>${v.ep.p?'（'+v.ep.p+'）':''}`:'特輯'}</div><img loading="lazy" src="${thumb(v.id)}" alt=""><div class="t">${esc(clean(v.title).replace(/[｜|]?\s*新加坡故事\s*(EP\s*\d+)?\s*(（[上中下]）)?[｜|─]?/i,' ').trim())}</div></div>`).join('')}
 ${s.playlist?`<a class="btn ghost" href="https://www.youtube.com/playlist?list=${s.playlist}" target="_blank" rel="noopener">在 YouTube 依序播放</a>`:''}</div>`}).join('')
 +`<div class="card"><b>更多專題</b><p style="font-size:14px;color:var(--mute);margin:4px 0 0">台美安全、兩岸交流等系列整理中，敬請期待。</p></div>`}
const postCard=p=>`<div class="card post" data-p="${esc(p.file||p.url)}"><div class="k">${p.type==='slides'?'📊 簡報':'📝 文章'}・${esc(p.date)}</div><div class="pt">${esc(p.title)}</div>${p.summary?`<div class="ps">${esc(p.summary)}</div>`:''}</div>`;
function posts(){view.innerHTML=`<h2>簡報／文章</h2>`+(POSTS.length?POSTS.map(postCard).join(''):'<div class="empty">尚無文章</div>')}
function about(){view.innerHTML=`<div class="card" style="text-align:center"><img src="icons/icon-192.png" style="width:96px;border-radius:20px" alt=""><h2 style="justify-content:center">${esc(CFG.name)}</h2><p style="font-size:15px">${esc(CFG.about)}</p>
 <a class="btn" href="${subUrl}" target="_blank" rel="noopener">▶ 訂閱 YouTube 頻道</a></div><div class="card"><b>連結</b><br>${CFG.links.map(l=>`<a class="btn ghost" href="${l.url}" target="_blank" rel="noopener">${esc(l.label)}</a>`).join('')}<button class="btn ghost" id="share">分享這個 App</button></div>
 <div class="card" style="font-size:14px"><b>加到手機主畫面</b><br>iPhone：Safari 下方「分享」→「加入主畫面」。<br>Android：Chrome 右上「⋮」→「安裝應用程式」或「加到主畫面」。</div><div class="upd">影片 ${longs().length} 支・短影音 ${shorts().length} 支・資料更新 ${UPD?new Date(UPD).toLocaleString('zh-TW'):'—'}</div>`;
 $('#share').onclick=async()=>{const d={title:CFG.name,url:location.href.split('#')[0]};if(navigator.share)navigator.share(d).catch(()=>{});else{await navigator.clipboard?.writeText(d.url);toast('已複製連結')}}}
function openSheet(h){sheetbody.innerHTML=h;sheet.hidden=false;document.body.style.overflow='hidden'}
function closeSheet(){sheet.hidden=true;sheetbody.innerHTML='';document.body.style.overflow=''}
function playVideo(id){const v=V.find(x=>x.id===id)||{id,title:''};
 openSheet(`<div class="embed ${v.short?'vert':''}"><iframe src="https://www.youtube-nocookie.com/embed/${id}?autoplay=1&rel=0&playsinline=1" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen></iframe></div>
 <h3 style="font-family:'Noto Serif TC',serif;line-height:1.5;margin:12px 0 4px">${esc(clean(v.title))}</h3><div class="m" style="color:var(--mute);font-size:13px">${v.published?fmtD(v.published):''}</div>
 <a class="btn" href="${subUrl}" target="_blank" rel="noopener">訂閱頻道</a><a class="btn ghost" href="${yt(id)}" target="_blank" rel="noopener">在 YouTube 觀看</a><button class="btn ghost" data-share="${id}">分享</button>
 ${v.desc?`<p style="font-size:14px;color:#c9c2b0;white-space:pre-line">${esc(v.desc)}</p>`:''}`)}
function md(s){s=s.replace(/^---\n[\s\S]*?\n---\n/,'');const L=s.split('\n');let o='',inL='';const il=t=>esc(t).replace(/!\[([^\]]*)\]\(([^)]+)\)/g,'<img alt="$1" src="$2">').replace(/\[([^\]]+)\]\(([^)]+)\)/g,'<a href="$2" target="_blank" rel="noopener">$1</a>').replace(/\*\*(.+?)\*\*/g,'<b>$1</b>').replace(/\*(.+?)\*/g,'<i>$1</i>').replace(/`(.+?)`/g,'<code>$1</code>');
 const close=()=>{if(inL){o+=`</${inL}>`;inL=''}};
 for(const l of L){let m;if(m=l.match(/^(#{1,3})\s+(.*)/)){close();o+=`<h${m[1].length}>${il(m[2])}</h${m[1].length}>`}else if(m=l.match(/^\s*[-*]\s+(.*)/)){if(inL!=='ul'){close();o+='<ul>';inL='ul'}o+=`<li>${il(m[1])}</li>`}
  else if(m=l.match(/^\s*\d+\.\s+(.*)/)){if(inL!=='ol'){close();o+='<ol>';inL='ol'}o+=`<li>${il(m[1])}</li>`}else if(m=l.match(/^>\s?(.*)/)){close();o+=`<blockquote>${il(m[1])}</blockquote>`}
  else if(!l.trim())close();else{close();o+=`<p>${il(l)}</p>`}}close();return o}
async function openPost(f){const p=POSTS.find(x=>(x.file||x.url)===f);if(!p)return;const vid=p.video?`<div class="v card" data-id="${p.video}" style="display:flex;gap:10px;align-items:center"><img src="${thumb(p.video)}" style="width:40%" alt=""><div><div class="k" style="font-size:12px;color:var(--gold)">相關影片</div>${esc(clean((V.find(v=>v.id===p.video)||{}).title||'觀看影片'))}</div></div>`:'';
 if(p.type==='slides'){const u=p.file||p.url;openSheet(`<div style="margin-top:44px"><div class="k" style="color:var(--gold);font-size:12px">📊 簡報・${esc(p.date)}</div><h2>${esc(p.title)}</h2><a class="btn" href="${esc(u)}" target="_blank" rel="noopener">開啟／下載簡報</a><iframe class="pdf" src="${esc(u)}" style="margin-top:12px"></iframe>${vid}</div>`);return}
 let body='';try{body=md(await (await fetch(p.file)).text())}catch(e){body='<p>離線中，無法載入文章。</p>'}
 openSheet(`<div class="md" style="margin-top:44px"><div style="color:var(--gold);font-size:12px">📝 文章・${esc(p.date)}</div>${body}</div>${vid}<a class="btn" href="${subUrl}" target="_blank" rel="noopener">訂閱頻道</a>`)}
const R={home,videos,series,posts,about};
function go(v){if(!R[v])v='home';document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('on',b.dataset.v===v));R[v]();scrollTo(0,0);if(location.hash!=='#'+v)history.replaceState(null,'','#'+v)}
document.querySelector('nav').onclick=e=>{const b=e.target.closest('button');if(b)go(b.dataset.v)};
document.addEventListener('click',async e=>{const s=e.target.closest('[data-share]');if(s){const d={title:CFG.name,url:yt(s.dataset.share)};if(navigator.share)navigator.share(d).catch(()=>{});else{await navigator.clipboard?.writeText(d.url);toast('已複製影片連結')}return}
 const v=e.target.closest('[data-id]');if(v){playVideo(v.dataset.id);return}const p=e.target.closest('[data-p]');if(p)openPost(p.dataset.p)});
sheet.onclick=e=>{if(e.target===sheet||e.target.classList.contains('close'))closeSheet()};
(async()=>{try{const[a,b]=await Promise.all([fetch('data/videos.json').then(r=>r.json()),fetch('data/posts.json').then(r=>r.json())]);V=a.videos;PL=a.playlists||{};UPD=a.updated;POSTS=b.posts||[]}catch(e){toast('資料載入失敗')}go(location.hash.slice(1))})();
if('serviceWorker'in navigator)navigator.serviceWorker.register('sw.js');
