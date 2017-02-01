(function(define) {
    'use strict';
    define(['jquery', 'jquery.cookie'], function($) {
        var EmailOptInInterface = {

            urls: {
                emailOptInUrl: '/user_api/v1/preferences/email_opt_in/'
            },

            headers: {
                'X-CSRFToken': $.cookie('csrftoken')
            },

            /**
             * Set the email opt in setting for the organization associated
             * with this course.
             * @param  {string} courseKey  Slash-separated course key.
             * @param {string} emailOptIn The preference to opt in or out of organization emails.
             */
            setPreference: function(courseKey, emailOptIn) {
                return $.ajax({
                    url: this.urls.emailOptInUrl,
                    type: 'POST',
                    data: {course_id: courseKey, email_opt_in: emailOptIn},
                    headers: this.headers
                });
            }
        };

        return EmailOptInInterface;
    });
}).call(this, define || RequireJS.define);
