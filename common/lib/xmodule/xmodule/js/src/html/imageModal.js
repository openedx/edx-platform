$(function() {
  $("a.zoomable").each(function() {
    var smallImageObject = $(this).children();
    var largeImageSRC = $(this).attr('href');
    
    // if contents of zoomable link is image and large image link exists: setup modal
    if (smallImageObject.is('img') && largeImageSRC) {
      var smallImageHTML = $(this).html();
      var largeImageHTML = '<img alt="" src="' + largeImageSRC + '" />';
      var imageModalHTML =
        '<div class="imageModal-link">' +
          smallImageHTML +
          '<i class="icon-resize-full icon-3x"></i></div>' +
        '<div class="imageModal"><div class="imageModal-content">' +
          largeImageHTML +
          '<i class="icon-remove icon-3x"></div></div>';
      $(this).replaceWith(imageModalHTML);
    }
  });
  
  $(".imageModal-link").click(function() {
    $(this).siblings(".imageModal").show();
  });
  
  var imageModalContentHover = false;
  $(".imageModal-content").hover(function() {
    imageModalContentHover = true;
  }, function() {
    imageModalContentHover = false;
  });
  
  $(".imageModal").click(function() {
    if (!imageModalContentHover){
      $(this).hide();
    }
  });
  $(".imageModal-content i.icon-remove").click(function() {
    $(this).closest(".imageModal").hide();
  });
});