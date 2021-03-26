$(document).ready(function() {
    'use strict';

    $('.generate_certs').click(function(e) {
        e.preventDefault();
        var post_url = $('.generate_certs').data('endpoint');
        $('.generate_certs').attr('disabled', true).addClass('is-disabled').attr('aria-disabled', true);
        $.ajax({
            type: 'POST',
            url: post_url,
            dataType: 'text',
            success: function() {
                location.reload();
            },
            error: function(jqXHR, textStatus, errorThrown) {
                $('#errors-info').text(jqXHR.responseText);
                $('.generate_certs').attr('disabled', false).removeClass('is-disabled').attr('aria-disabled', false);
            }
        });
    });
});
