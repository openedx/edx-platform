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

function submitForms(id_array) {
    var get_data = [];
    for (var i=0;i<id_array.length;i++){
        get_data.push.apply(get_data, $('#'+id_array[i]).serializeArray());
    }
    console.log(get_data);
    var url = document.URL.split("?")[0]+"?";
    for (var o in get_data){
        url = url + (get_data[o].name + "=" +get_data[o].value + "&");
    }
    document.location.href = url.substring(0, url.length-1);
}

function searchHandle(e, id_array){
    e.preventDefault();
    if(e.keyCode === 13){
        submitForms(id_array);
    }
}

$(document).ready(function() {
    $('.scaled-text').textfill({ maxFont: 36 });
});