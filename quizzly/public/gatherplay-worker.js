const CACHE = 'gatherplay-static-v2';
const FONT = '/assets/quizzly/fonts/noto-sans-ethiopic.ttf';
const OFFLINE = '/assets/quizzly/gatherplay-offline.html';
self.addEventListener('install', event => event.waitUntil(caches.open(CACHE).then(cache => cache.addAll([OFFLINE,FONT]))));
self.addEventListener('activate', event => event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k=>k.startsWith('gatherplay-static-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch', event => {
  const request=event.request,url=new URL(request.url);
  if(request.method!=='GET'||url.origin!==self.location.origin)return;
  if(request.mode==='navigate'&&url.pathname.startsWith('/play/')){
    event.respondWith(fetch(request).catch(()=>caches.match(OFFLINE)));return;
  }
  if(url.pathname===FONT){event.respondWith(caches.match(FONT).then(hit=>hit||fetch(request)));return;}
  // Only immutable public build files. Never API, HTML sessions, uploads or receipts.
  if(/^\/assets\/quizzly\/frontend\/assets\/[^/]+-[a-f0-9]{8}\.(js|css|woff2)$/.test(url.pathname)){
    event.respondWith(caches.match(request).then(hit=>hit||fetch(request).then(response=>{if(response.ok){const copy=response.clone();caches.open(CACHE).then(cache=>cache.put(request,copy));}return response;})));
  }
});
