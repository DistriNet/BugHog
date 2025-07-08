window.addEventListener("load", function onLoad(event) {
    setTimeout(() => {
        var downloadLink = document.getElementById("download-link");
        downloadLink.click();
    }, 10000);
});