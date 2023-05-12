$(document).ready(function() {
    'use strict';

    $('.generate_certs').click(function(e) {
        e.preventDefault();
        // eslint-disable-next-line camelcase
        var post_url = $('.generate_certs').data('endpoint');
        $('.generate_certs').attr('disabled', true).addClass('is-disabled').attr('aria-disabled', true);
        $.ajax({
            type: 'POST',
            // eslint-disable-next-line camelcase
            url: post_url,
            dataType: 'text',
            success: function() {
                location.reload();
            },
            // eslint-disable-next-line no-unused-vars
            error: function(jqXHR, textStatus, errorThrown) {
                $('#errors-info').text(jqXHR.responseText);
                $('.generate_certs').attr('disabled', false).removeClass('is-disabled').attr('aria-disabled', false);
            }
        });
    });
});
