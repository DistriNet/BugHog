"use strict";

window.addEventListener("load", function onLoad(event) {
    setTimeout(function () {
        var downloadLink = document.getElementById("download-link");
        downloadLink.click();
    }, 1000);
});