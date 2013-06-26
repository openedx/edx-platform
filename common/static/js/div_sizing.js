;(function($) {
    $.fn.textfill = function(options) {
        var fontSize = options.maxFont;
        var ourText = $('span:visible:first', this);
        var maxHeight = $(this).height();
        var maxWidth = $(this).width();
        var textHeight;
        var textWidth;
        do {
            ourText.css('font-size', fontSize);
            textHeight = ourText.height();
            textWidth = ourText.width();
            fontSize = fontSize - 1;
        } while ((textHeight > maxHeight || textWidth > maxWidth) && fontSize > 3);
        return this;
    };
})(jQuery);

$(document).ready(function() {
    $('.scaled-text').textfill({ maxFont: 36 });
});