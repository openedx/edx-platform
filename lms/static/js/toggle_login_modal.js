(function($){
  $.fn.extend({
    leanModal: function(options) {
      var defaults = {
        top: 100,
        overlay: 0.5,
        closeButton: null,
        position: 'fixed'
      }

      var overlay = $("<div id='lean_overlay'></div>");
      $("body").append(overlay);

      options =  $.extend(defaults, options);

      return this.each(function() {
        var o = options;

        $(this).click(function(e) {

          $(".modal").hide();

          var modal_id = $(this).attr("href");

          $("#lean_overlay").click(function() {
             close_modal(modal_id);
          });

          $(o.closeButton).click(function() {
             close_modal(modal_id);
          });

          var modal_height = $(modal_id).outerHeight();
          var modal_width = $(modal_id).outerWidth();

          $('#lean_overlay').css({ 'display' : 'block', opacity : 0 });
          $('#lean_overlay').fadeTo(200,o.overlay);

          $('iframe', modal_id).attr('src', $('iframe', modal_id).data('src'));
          $(modal_id).css({
            'display' : 'block',
            'position' : o.position,
            'opacity' : 0,
            'z-index': 11000,
            'left' : 50 + '%',
            'margin-left' : -(modal_width/2) + "px",
            'top' : o.top + "px"
          })

          $(modal_id).fadeTo(200,1);
          e.preventDefault();

        });
      });

      function close_modal(modal_id){
        $("#lean_overlay").fadeOut(200);
        $('iframe', modal_id).attr('src', '');
        $(modal_id).css({ 'display' : 'none' });
      }
    }
  });

  $("a[rel*=leanModal]").each(function(){
    $(this).leanModal({ top : 120, overlay: 1, closeButton: ".close-modal", position: 'absolute' });
    embed = $($(this).attr('href')).find('iframe')
    if(embed.length > 0) {
      embed.data('src', embed.attr('src') + '?autoplay=1');
      embed.attr('src', '');
    }
  });
})(jQuery);
