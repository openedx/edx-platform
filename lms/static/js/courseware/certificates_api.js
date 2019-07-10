$(document).ready(function() {
    'use strict';

    $('.generate_certs').click(function(e) {
        e.preventDefault();
        var post_url = $('.generate_certs').data('endpoint');
        var student_id = $('.generate_certs').data('student_id');
        $('.generate_certs').attr('disabled', true).addClass('is-disabled').attr('aria-disabled', true);
        $.ajax({
            type: 'POST',
            url: post_url,
            dataType: 'text',
            data: {
                'student_id': student_id
            },
            success: function() {
                location.reload();
            },
            error: function(jqXHR, textStatus, errorThrown) {
                $('#errors-info').html(jqXHR.responseText);
                $('.generate_certs').attr('disabled', false).removeClass('is-disabled').attr('aria-disabled', false);
            }
        });
    });
});
