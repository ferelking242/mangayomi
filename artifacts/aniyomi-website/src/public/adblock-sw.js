const AD_DOMAINS = [
  'doubleclick.net', 'googlesyndication.com', 'googleadservices.com',
  'googletagservices.com', 'googletagmanager.com', 'ads.yahoo.com',
  'adservice.google.com', 'amazon-adsystem.com', 'adnxs.com',
  'taboola.com', 'outbrain.com', 'popads.net', 'adsterra.com',
  'propellerads.com', 'revcontent.com', 'media.net',
  'yandexadexchange.net', 'smartadserver.com', 'rubiconproject.com',
  'openx.net', 'criteo.com', 'adsrvr.org',
]

self.addEventListener('install', () => self.skipWaiting())
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()))

self.addEventListener('fetch', event => {
  try {
    const url = new URL(event.request.url)
    const isAd = AD_DOMAINS.some(domain => url.hostname.endsWith(domain))
    if (isAd) {
      event.respondWith(new Response('', {
        status: 200,
        headers: { 'Content-Type': 'text/plain' },
      }))
    }
  } catch {}
})
