"use strict";

window.addEventListener("load", function () {
    var iframe = document.getElementById("iframe");

    setTimeout(function () {
        iframe.contentWindow.location.href = "about:blank";

        setTimeout(function () {
            var iframeDocument = iframe.contentWindow.document;
            var image = iframeDocument.createElement("img");
            image.src = "/report/?leak=c957606";
            iframeDocument.body.appendChild(image);
        }, 1000);
    }, 2000);
});