"use strict";

window.addEventListener("load", function () {
    var iframe = document.getElementById("iframe");

    setTimeout(function () {
        iframe.contentWindow.location.href = "about:blank";

        setTimeout(function () {
            var iframeDocument = iframe.contentWindow.document;
            var object = iframeDocument.createElement("object");
            object.data = "/report/?leak=c957606-object";
            iframeDocument.body.appendChild(object);
        }, 1000);
    }, 2000);
});