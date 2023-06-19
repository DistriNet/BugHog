"use strict";

var iframeHref = document.querySelector("#iframe_href");
iframeHref.addEventListener('load', function () {
if (document.getElementById("iframe_href").contentWindow.document.body.innerHTML.indexOf("IT WORKED") > -1) {
    document.location.href = "https://adition.com/report/?leak=c909865";
}

iframeHref.contentWindow.location.href = "javascript:'IT WORKED'";
});