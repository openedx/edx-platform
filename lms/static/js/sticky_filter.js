$(function() {
  var offset = $('.filter nav').offset().top;

  $(window).scroll(function() {
    if (offset <= window.pageYOffset) {
      return $('.filter nav').addClass('fixed-top');
    }
    else if (offset >= window.pageYOffset) {
      return $('.filter nav').removeClass('fixed-top');
    }
  });
});
