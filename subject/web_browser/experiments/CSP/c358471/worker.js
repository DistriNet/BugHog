// Content-Security-Policy: connect-src 'self'; script-src 'self' 'unsafe-inline'
// bughog_domain: leak.test
onmessage = function (event) {
  function reqListener() {
    postMessage("worker:pong");
  }
  try {
    var oReq = new XMLHttpRequest();
    oReq.onload = reqListener;
    oReq.open("get", "https://a.test/report/?bughog_reproduced=OK", true);
    oReq.send();
  } catch (e) {}

  importScripts("https://a.test/report/?bughog_reproduced=OK");
};
