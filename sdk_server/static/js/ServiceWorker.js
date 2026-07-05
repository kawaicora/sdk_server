self.addEventListener(
    'install', 
    e => { 
        e.waitUntil(caches.open('v1').then(
            cache => { 
                return cache.addAll(['/', '/view/main']); 
            })
        ); 
    }
);


self.addEventListener('fetch', e => {
  e.respondWith(
    caches.match(e.request).then(r => r || fetch(e.request))
  );
});



self.addEventListener('push', e => {
  const data = e.data.json();
  self.registration.showNotification(data.title, {
    body: data.body
  });
});

