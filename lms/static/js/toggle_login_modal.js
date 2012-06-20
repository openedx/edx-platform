$(document).ready(function () {
  $('a.login').click(function() {
    $('.modal-wrapper').addClass("visible");
  });
  $('div.close-modal').click(function() {
    $('.modal-wrapper').removeClass("visible");
  });
});
