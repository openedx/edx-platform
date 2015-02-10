var edx = edx || {};

(function($) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.EnrollmentInterface = {

        urls: {
            enrollment: '/api/enrollment/v1/enrollment',
            trackSelection: '/course_modes/choose/'
        },

        headers: {
            'X-CSRFToken': $.cookie('csrftoken')
        },

        /**
         * Enroll a user in a course, then redirect the user
         * to the track selection page.
         * @param  {string} courseKey  Slash-separated course key.
         */
        enroll: function( courseKey ) {
            var data_obj = {
                course_details: {
                    course_id: courseKey
                }
            };
            var data = JSON.stringify(data_obj);
            $.ajax({
                url: this.urls.enrollment,
                type: 'POST',
                contentType: 'application/json; charset=utf-8',
                data: data,
                headers: this.headers,
                context: this
            })
            .fail(function( jqXHR ) {
                var responseData = JSON.parse(jqXHR.responseText);
                if ( jqXHR.status === 403 && responseData.user_message_url ) {
                    // Check if we've been blocked from the course
                    // because of country access rules.
                    // If so, redirect to a page explaining to the user
                    // why they were blocked.
                    this.redirect( responseData.user_message_url );
                }
                else {
                    // Otherwise, go to the track selection page as usual.
                    // This can occur, for example, when a course does not
                    // have a free enrollment mode, so we can't auto-enroll.
                    this.redirect( this.trackSelectionUrl( courseKey ) );
                }
            })
            .done(function() {
                // If we successfully enrolled, go to the track selection
                // page to allow the user to choose a paid enrollment mode.
                this.redirect( this.trackSelectionUrl( courseKey ) );
            });
        },

        /**
         * Construct the URL to the track selection page for a course.
         * @param  {string} courseKey Slash-separated course key.
         * @return {string} The URL to the track selection page.
         */
        trackSelectionUrl: function( courseKey ) {
            return this.urls.trackSelection + courseKey + '/';
        },

        /**
         * Redirect to a URL.  Mainly useful for mocking out in tests.
         * @param  {string} url The URL to redirect to.
         */
        redirect: function(url) {
            window.location.href = url;
        }
    };
})(jQuery);
