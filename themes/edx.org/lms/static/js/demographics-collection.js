$(document).ready(function() {
    'use strict';

    $('#demographics-dismiss').click(function(event) {
        event.preventDefault();
        return $.ajax({
            url: '/api/demographics/v1/demographics/status/',
            type: 'PATCH',
            headers: {
                'X-CSRFToken': $.cookie('csrftoken')
            },
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify({
                show_call_to_action: false
            }),
            context: this,
            success: function() {
                $('#demographics-banner-link').hide();
            }
        });
    });
});
