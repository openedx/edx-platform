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
    submitForms(false);
}

function submitForms(retain_page) {
    var get_data = [];
<<<<<<< HEAD
    var form_list = $(".auto-submit .parameter");
=======
    var form_list = $(".auto-submit input");
>>>>>>> Added extra javascript for performant and smooth user interaction
    for (var i in form_list){
        get_data.push.apply(get_data, form_list.eq(i).serializeArray());
    }
    var url = document.URL.split("?")[0]+"?";
    for (var o in get_data){
        if (retain_page === false){
            if (get_data[o].name == "page"){
                get_data[o].value = 1;
            }
        }
        url = url + (get_data[o].name + "=" +get_data[o].value + "&");
    }
    document.location.href = url.substring(0, url.length-1);
}

function incrementPage(){
    var current_page = $("#current-page input");
    current_page[0].value++;
    submitForms(true);
}

function decrementPage(){
    var current_page = $("#current-page input");
    current_page[0].value--;
    submitForms(true);
}

function clickHandle(e, retain_page){
    e.preventDefault();
    submitForms(retain_page);
}

function searchHandle(e, retain_page){
    if(e.keyCode === 13){
        e.preventDefault();
        submitForms(retain_page);
    }
}

function changeHandler(input, max_pages){
    if (input.value < 1) {input.value=1;}
    if (input.value > max_pages) {input.value=max_pages;}
}

function filterTrigger(input, type, retain_page){
    if (type == "org"){
        $("#selected-org").val($($(input).children(":first")).text());
    }

    if (type == "course"){
        $("#selected-course").val($(input).children(":first").text());
    }

    submitForms(retain_page);
}

$(document).ready(function() {
    $('.scaled-text').textfill({ maxFont: 36 });
});