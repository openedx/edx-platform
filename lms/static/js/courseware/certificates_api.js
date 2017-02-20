$(document).ready(function() {
    'use strict';

    $('.generate_certs').click(function(e) {
        e.preventDefault();
        var request_cert_btn = $('.generate_certs');
        request_cert_btn.attr('disabled', true).addClass('is-disabled').attr('aria-disabled', true);
        $.ajax({
            type: 'POST',
            url: request_cert_btn.data('endpoint'),
            data: {
                username: request_cert_btn.data('username')
            },
            dataType: 'text',
            success: function() {
                location.reload();
            },
            error: function(jqXHR, textStatus, errorThrown) {
                $('#errors-info').html(jqXHR.responseText);
                request_cert_btn.attr('disabled', false).removeClass('is-disabled').attr('aria-disabled', false);
            }
        });
    });
});
