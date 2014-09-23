/**
Student profile page.  This is where students can update
their profile information, which includes demographic information
and preferences.
**/

var edx = edx || {};
edx.studentProfile = (function($) {
    'use strict';

    /**
    Retrieve a cookie value.

    NOTE: we will pull this into its own helper module eventually,
    since it is duplicated in the student account JS.

    Arguments:
        name (string): The name of the cookie.

    Returns:
        string

    **/
    var getCookie = function(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = $.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    };

    var _module = {
        /**
        Save the user's profile information.
        **/
        save: function() {
            // perform validation?
            $.ajax({
                url: "name_change",
                type: "PUT",
                data: {
                    new_name: $("#new-name").val()
                }
            });
        },

        eventHandlers: {
            /**
            Initialize event handlers.
            **/
            init: function() {
                // Ensure that we're sending the CSRF token with AJAX requests
                $.ajaxSetup({ beforeSend: this.beforeAjaxSend });

                // Install an event handler for the form
                $("#name-change-form").submit(this.submit);
            },

            /**
            Add the CSRF token (retrieved from the user's cookies)
            to outgoing PUT requests.
            **/
            beforeAjaxSend: function(xhr, settings) {
                if (settings.type === "PUT") {
                    var csrftoken = getCookie('csrftoken');
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            },

            /**
            Handle submission of the form.
            **/
            submit: function(event) {
                event.preventDefault();
                this.save();
            }
        }
    };

    // Initalize when the document is ready
    $(document).ready(_module.eventHandlers.init);

    return _module;
})(jQuery);


