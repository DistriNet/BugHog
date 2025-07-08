"use strict";

function report_only_log(variable, value) {
    console.log("+++bughog_" + variable + "=" + value + "+++");
}

function report_only_request(variable, value, domain) {
    var url = "";
    var path = "/report/?bughog_" + variable + "=" + value;
    if (domain) {
        url = "//" + domain + path;
    } else {
        url = path;
    }
    var img = document.createElement('img');
    img.src = url;
    document.body.appendChild(img);
}

function report(variable, value, domain) {
    report_only_log(variable, value);
    report_only_request(variable, value, domain);
}

function reproduced(domain) {
    var variable = 'reproduced';
    var value = 'OK';
    report_only_log(variable, value);
    report_only_request(variable, value, domain);
}
