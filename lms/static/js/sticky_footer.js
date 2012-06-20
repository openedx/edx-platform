$(function() {
  var stickyFooter = function(){
    var pageHeight = $('html').height();
    var windowHeight = $(window).height();
    var footerHeight = $('footer').outerHeight();

    var totalHeight = $('footer').hasClass('fixed-bottom') ? pageHeight + footerHeight : pageHeight;


      if (windowHeight < totalHeight) {
        return $('footer').removeClass('fixed-bottom');
      } else {
        return $('footer').addClass('fixed-bottom');
      }
  };

  stickyFooter();

  $(window).resize(function() {
    console.log("resizing");
    stickyFooter();
  });
});
