
const blob = new Blob(["<html><body><script src=\"data:application/javascript,document.location.href='https://adition.com/report/?leak=c1115298';\"></script><meta http-equiv='refresh' content='2;url=https://adition.com/custom/c1115298/helper'></body></html>"], {type : "text/html"});

onload = function () {
	open(URL.createObjectURL(blob));
}