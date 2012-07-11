$(document).ready(function () {
  $('a#login').click(function() {
    $('.modal.login-modal').addClass("visible");
    $('.modal-overlay').addClass("visible");
  });
  $('div.close-modal').click(function() {
    $('.modal.login-modal').removeClass("visible");
    $('.modal-overlay').removeClass("visible");
  });

  $('a#signup').click(function() {
    $('.modal.signup-modal').addClass("visible");
    $('.modal-overlay').addClass("visible");
  });
  $('div.close-modal').click(function() {
    $('.modal.signup-modal').removeClass("visible");
    $('.modal-overlay').removeClass("visible");
  });

  $('.hero').click(function() {
    $('.modal.video-modal').addClass("visible");
    $('.modal-overlay').addClass("visible");
  });
  $('div.close-modal').click(function() {
    $('.modal.video-modal').removeClass("visible");
    $('.modal-overlay').removeClass("visible");
  });
});

