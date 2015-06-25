$(document).ready(function() {
    'use strict';

    $("#btn_generate_cert").click(function(e){
        e.preventDefault();
        var post_url = $("#btn_generate_cert").data("endpoint");
        $('#btn_generate_cert').prop("disabled", true);
        $.ajax({
            type: "POST",
            url: post_url,
            dataType: 'text',
            success: function () {
                location.reload();
            },
            error: function(jqXHR, textStatus, errorThrown) {
                $('#errors-info').html(jqXHR.responseText);
                $('#btn_generate_cert').prop("disabled", false);
            }
        });
    });
});
