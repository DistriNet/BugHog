onmessage = function (event) {


  function reqListener () {
      postMessage("worker:pong");
  }
  try {
    var oReq = new XMLHttpRequest();
    oReq.onload = reqListener;
    oReq.open("get", "https://adition.com/report/?leak=c358471-xhr", true);
    oReq.send();
  } catch (e) {
  }

  importScripts("https://adition.com/report/?leak=c358471");

};