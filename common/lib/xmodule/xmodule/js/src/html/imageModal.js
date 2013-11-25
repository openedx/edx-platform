$(function() {
  
  // Set up on page load
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
          '<i class="icon-fullscreen icon-3x"></i>' +
        '</div>' +
        '<div class="imageModal"><div class="imageModal-content">' +
          '<div class="imageModal-imgWrapper">' + largeImageHTML + '</div>' +
          '<i class="icon-remove icon-3x"></i>' +
          '<div class="imageModal-zoom"><i class="icon-zoom-in icon-3x"></i><i class="icon-zoom-out icon-3x"></i></div></div>' +
        '</div>';
      $(this).replaceWith(imageModalHTML);
    }
  });


  // Opening and closing image modal on clicks
  $(".imageModal-link").click(function() {
    $(this).siblings(".imageModal").show();
    $(this).siblings(".imageModal").find(".imageModal-imgWrapper img").css({top: 0, left: 0, });
    $(this).siblings(".imageModal").find(".imageModal-imgWrapper").css({left: 0, top: 0, width: 'auto', height: 'auto'});
    $('html').css({overflow: 'hidden'});
  });
  
  var imageModalImageHover = false;
  $(".imageModal-content img, .imageModal-content .imageModal-zoom").hover(function() {
    imageModalImageHover = true;
  }, function() {
    imageModalImageHover = false;
  });
  
  $(".imageModal").click(function() {
    if (!imageModalImageHover){
      $(this).hide();
      $('.imageModal-content .imageModal-imgWrapper img', this).removeClass("draggable").removeClass('zoomed').draggable( 'destroy' );
      $('html').css({overflow: 'auto'});
    }
  });
  $(".imageModal-content i.icon-remove").click(function() {
    $(this).closest(".imageModal").hide();
    // Remove draggable from 
    $(this).siblings('img').removeClass("draggable").removeClass('zoomed').draggable( 'destroy' );
    $('html').css({overflow: 'auto'});
  });


  // zooming image in modal and allow it to be dragged
  // Make sure it always starts zero position for below calcs to work
  
  $(".imageModal-content .imageModal-zoom i").click(function() {
    var mask = $(this).closest(".imageModal-content");
    
    var img = $(this).closest(".imageModal").find("img");
    
    if ($(this).hasClass('icon-zoom-in')) {
      img.addClass('zoomed');
      
      var imgWidth   = img.width();
      var imgHeight  = img.height();
      
      var imgContainerOffsetLeft = imgWidth - mask.width();
      var imgContainerOffsetTop = imgHeight - mask.height();
      var imgContainerWidth = imgWidth + imgContainerOffsetLeft;
      var imgContainerHeight = imgHeight + imgContainerOffsetTop;
      
      img.parent().css({left: -imgContainerOffsetLeft, top: -imgContainerOffsetTop, width: imgContainerWidth, height: imgContainerHeight});
      img.css({top: imgContainerOffsetTop / 2, left: imgContainerOffsetLeft / 2});
      
      if (img.hasClass('draggable')) {
        img.draggable( 'enable' );
      } else {
        img.addClass("draggable").draggable({ containment: 'parent' });
      }
      
    } else if ($(this).hasClass('icon-zoom-out')) {
      img.draggable('disable').css({top: 0, left: 0, }).removeClass('zoomed');
      img.parent().css({left: 0, top: 0, width: 'auto', height: 'auto'});
    }
  });
});