'use strict';

var throw_func = function throw_func() {
  throw TypeError('SomeError');
};

var draw_image = function draw_image() {
  var img = document.createElement('img');
  img.src = 'https://www.gstatic.com/images/branding/googlelogo/2x/googlelogo_dark_color_84x28dp.png';
  document.body.appendChild(img);
};

setTimeout(function () {
  var error_message = document.getElementsByTagName("p")[0].innerHTML;
  if (error_message.indexOf("secret_info=123") > -1) {
    document.location.href = "https://adition.com/report/?leak=c1074317";
  }
}, 1000);