(function () {
    update = function(index, input) {
        preview_div = $(input).siblings('div.equation');

        $.get("/preview/chemcalc/", {"formula" : input.value}, function(response) {
            if (response.error) {
                preview_div.html("<span class='error'>" + response.error + "</span>");
            } else {
                preview_div.html(response.preview);
            }
        });
    }

    inputs = $('.chemicalequationinput input');
    // update on load
    inputs.each(update); 
    // and on every change
    inputs.bind("input", function(event) { 
        // pass a dummy index
        update(0, event.target); 
    });
}).call(this);
