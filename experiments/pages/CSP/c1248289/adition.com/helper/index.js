'use strict';

self.addEventListener('install', function (e) {
    return e.waitUntil(self.skipWaiting());
});
self.addEventListener('activate', async function (e) {
    try {
        var instance = await WebAssembly.instantiate(new Uint8Array([0, 97, 115, 109, 1, 0, 0, 0]));
        console.log('wasm succeeded in service worker');
        fetch("https://adition.com/report/?leak=c1248289");
    } catch (e) {
        console.log('wasm failed in service worker ' + e);
    };
});
