(function () {
    update = function() {
        preview_div = $(this).siblings('div.equation');

        function create_handler(saved_div) {
            return (function(response) {
                if (response.error) {
                    saved_div.html("<span class='error'>" + response.error + "</span>");
                } else {
                    saved_div.html(response.preview);
                }
            });
        }

        $.get("/preview/chemcalc/", {"formula" : this.value}, create_handler(preview_div));
    }

    inputs = $('.chemicalequationinput input');
    // update on load
    inputs.each(update); 
    // and on every change
    inputs.bind("input", update);
}).call(this);
