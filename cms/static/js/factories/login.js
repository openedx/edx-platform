define([
    'jquery.cookie',
    'utility',
    'common/js/components/utils/view_utils',
    'edx-ui-toolkit/js/utils/string-utils'
], function(
    cookie,
    utility,
    ViewUtils,
    StringUtils
) {
    'use strict';
    return function(homepageURL) {
        function postJSON(url, data, callback) {
            $.ajax({
                type: 'POST',
                url: url,
                dataType: 'json',
                data: data,
                success: callback
            });
        }

        // Clear the login error message when credentials are edited
        $('input#email').on('input', function() {
            $('#login_error').removeClass('is-shown');
        });

        $('input#password').on('input', function() {
            $('#login_error').removeClass('is-shown');
        });

        $('form#login_form').submit(function(event) {
            event.preventDefault();
            var submitButton = $('#submit'),
                deferred = new $.Deferred(),
                promise = deferred.promise();
            ViewUtils.disableElementWhileRunning(submitButton, function() { return promise; });
            var submit_data = $('#login_form').serialize();

            postJSON('/login_post', submit_data, function(json) {
                if (json.success) {
                    var next = /next=([^&]*)/g.exec(decodeURIComponent(window.location.search));
                    if (next && next.length > 1 && !isExternal(next[1])) {
                        ViewUtils.redirect(next[1]);
                    } else {
                        ViewUtils.redirect(homepageURL);
                    }
                } else if ($('#login_error').length === 0) {
                    $('#login_form').prepend(
                        StringUtils.interpolate(
                            '<div id="login_error" class="message message-status error">{value}</div>', {
                                value: json.value
                            }
                        )
                    );
                    $('#login_error').addClass('is-shown');
                    deferred.resolve();
                } else {
                    $('#login_error')
                        .stop()
                        .addClass('is-shown')
                        .html(json.value);
                    deferred.resolve();
                }
            });
        });
    };
});
