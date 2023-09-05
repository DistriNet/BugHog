onmessage = function (event) {
  function reqListener() {
    postMessage("worker:pong");
  }
  try {
    var oReq = new XMLHttpRequest();
    oReq.onload = reqListener;
    oReq.open("get", "https://a.test/report/?leak=c358471-xhr", true);
    oReq.send();
  } catch (e) {}

  importScripts("https://a.test/report/?leak=c358471");
};
