(function () {
    var preview_div = $('.chemicalequationinput .equation');
    $('.chemicalequationinput input').bind("input", function(eventObject) {
        $.get("/preview/chemcalc/", {"formula" : this.value}, function(response) {
            if (response.error) {
                preview_div.html("<span class='error'>" + response.error + "</span>");
            } else {
                preview_div.html(response.preview);
            }
          });
    });
}).call(this);
