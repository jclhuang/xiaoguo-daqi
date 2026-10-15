const C='xgdq-v1',F=['./','index.html','style.css','app.js','config.js','manifest.webmanifest','data/videos.json','data/posts.json','icons/icon-192.png','icons/icon-512.png','icons/apple-touch-icon.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(F)));self.skipWaiting()});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==C).map(x=>caches.delete(x)))));self.clients.claim()});
// 網路優先（拿最新影片/文章），離線時改用快取；縮圖也順便快取
self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return;const u=new URL(e.request.url);
 if(u.origin!==location.origin&&!u.hostname.endsWith('ytimg.com'))return;
 e.respondWith(fetch(e.request).then(r=>{const cp=r.clone();caches.open(C).then(c=>c.put(e.request,cp));return r}).catch(()=>caches.match(e.request,{ignoreSearch:true})))});
