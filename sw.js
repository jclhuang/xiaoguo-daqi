const C='xgdq-v12',F=['./','index.html','style.css','app.js','config.js','manifest.webmanifest','vendor/marked.min.js','data/videos.json','data/series.json','data/articles.json','data/podcast.json','data/podcast_feed.json','data/overrides.json','icons/icon-192.png','icons/icon-512.png','icons/apple-touch-icon.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(F)));self.skipWaiting()});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==C).map(x=>caches.delete(x)))));self.clients.claim()});
// 網路優先；PDF／音檔等只在打開過後才快取（不預先下載）。音檔的分段請求（Range）不快取。
self.addEventListener('fetch',e=>{const r=e.request;if(r.method!=='GET'||r.headers.has('range')||new URL(r.url).origin!==location.origin)return;
e.respondWith(fetch(r).then(res=>{if(res.ok&&res.status===200&&!/\.(mp3|m4a|aac|ogg|wav|opus)$/i.test(r.url)){const cp=res.clone();caches.open(C).then(c=>c.put(r,cp))}return res}).catch(()=>caches.match(r)))});
