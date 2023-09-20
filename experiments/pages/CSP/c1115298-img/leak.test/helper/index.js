const blob = new Blob(
  [
    "<html><body><img src='https://a.test/report/?leak=c1115298-img' /><meta http-equiv='refresh' content='2;url=https://a.test/CSP/c1115298/helper'></body></html>",
  ],
  { type: "text/html" }
);

onload = function () {
  open(URL.createObjectURL(blob));
};
