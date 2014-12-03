define(['jquery', 'jquery.cookie'], function($) {
    'use strict';
    return function () {
        $('form :input')
            .focus(function() {
                $('label[for="' + this.id + '"]').addClass('is-focused');
            })
            .blur(function() {
                $('label').removeClass('is-focused');
            });

        $('form#register_form').submit(function(event) {
            event.preventDefault();
            var submit_data = $('#register_form').serialize();

            $.ajax({
                url: '/create_account',
                type: 'POST',
                dataType: 'json',
                headers: {'X-CSRFToken': $.cookie('csrftoken')},
                notifyOnError: false,
                data: submit_data,
                success: function(json) {
                   location.href = '/course/';
                },
                error: function(jqXHR, textStatus, errorThrown) {
                   var json = $.parseJSON(jqXHR.responseText);
                   $('#register_error').html(json.value).stop().addClass('is-shown');
                }
            });
        });
    };
});
