(function($){
  $.fn.extend({
    /*
     * leanModal prepares an element to be a modal dialog.  Call it once on the
     * element that launches the dialog, when the page is ready.  This function
     * will add a .click() handler that properly opens the dialog.
     *
     * The launching element must:
     *   - be an <a> element, not a button,
     *   - have an href= attribute identifying the id of the dialog element,
     *   - have rel='leanModal'.
     */
    leanModal: function(options) {
      var defaults = {
        top: 100,
        overlay: 0.5,
        closeButton: null,
        position: 'fixed'
      }

      if ($("#lean_overlay").length == 0) {
        var overlay = $("<div id='lean_overlay'></div>");
        $("body").append(overlay);
      }

      options = $.extend(defaults, options);

      return this.each(function() {
        var o = options;

        $(this).click(function(e) {

          $(".modal").hide();

          var modal_id = $(this).attr("href");

          $("#lean_overlay").click(function(e) {
            close_modal(modal_id, e);
          });

          $(o.closeButton).click(function(e) {
            close_modal(modal_id, e);
          });

          // To enable closing of email modal when copy button hit
          $(o.copyEmailButton).click(function(e) {
            close_modal(modal_id, e);
          });

          var modal_height = $(modal_id).outerHeight();
          var modal_width = $(modal_id).outerWidth();

          $('#lean_overlay').css({ 'display' : 'block', opacity : 0 });
          $('#lean_overlay').fadeTo(200,o.overlay);

          $('iframe', modal_id).attr('src', $('iframe', modal_id).data('src'));
          if ($(modal_id).hasClass("email-modal")){
            $(modal_id).css({
              'width' : 80 + '%',
              'height' : 80 + '%',
              'position' : o.position,
              'opacity' : 0,
              'z-index' : 11000,
              'left' : 10 + '%',
              'top' : 10 + '%'
            })
          } else {
            $(modal_id).css({
              'position' : o.position,
              'opacity' : 0,
              'z-index': 11000,
              'left' : 50 + '%',
              'margin-left' : -(modal_width/2) + "px",
              'top' : o.top + "px"
            })
        }

          $(modal_id).show().fadeTo(200,1);
          $(modal_id).find(".notice").hide().html("");
          var notice = $(this).data('notice')
          if(notice !== undefined) {
            $notice = $(modal_id).find(".notice");
            $notice.show().html(notice);
            // This is for activating leanModal links that were in the notice. We should have a cleaner way of
            // allowing all dynamically added leanmodal links to work.
            $notice.find("a[rel*=leanModal]").leanModal({ top : 120, overlay: 1, closeButton: ".close-modal", position: 'absolute' });
          }
          window.scrollTo(0, 0);
          // InterSystems: play modal video 
          $(modal_id + ' video').each(function() {this.play()});          
          e.preventDefault();
        });
      });

      function close_modal(modal_id, e) {
        $("#lean_overlay").fadeOut(200);
        $('iframe', modal_id).attr('src', '');
        $(modal_id).css({ 'display' : 'none' });
        if (modal_id == '#modal_clone') {
          $(modal_id).remove();
        }
        e.preventDefault();
      }
    }
  });

  $(document).ready(function ($) {
    $("a[rel*=leanModal]").each(function () {
      $(this).leanModal({ top : 120, overlay: 1, closeButton: ".close-modal", position: 'absolute' });
      embed = $($(this).attr('href')).find('iframe')
      if (embed.length > 0 && embed.attr('src')) {
        var sep = (embed.attr('src').indexOf("?") > 0) ? '&' : '?';
        embed.data('src', embed.attr('src') + sep + 'autoplay=1&rel=0');
        embed.attr('src', '');
      }
    });
  });
})(jQuery);
