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

function correctionLink(event, spelling_correction){
    $("#searchbox")[0].value = spelling_correction;
    submitForms();
}

function submitForms() {
    var get_data = [];
    var form_list = $(".auto-submit");
    for (var i in form_list){
        get_data.push.apply(get_data, form_list.eq(i).serializeArray());
    }
    var url = document.URL.split("?")[0]+"?";
    for (var o in get_data){
        url = url + (get_data[o].name + "=" +get_data[o].value + "&");
    }
    document.location.href = url.substring(0, url.length-1);
}

function searchHandle(e, id_array){
    if(e.keyCode === 13){
        e.preventDefault();
        submitForms(id_array);
    }
}

$(document).ready(function() {
    $('.scaled-text').textfill({ maxFont: 36 });
});