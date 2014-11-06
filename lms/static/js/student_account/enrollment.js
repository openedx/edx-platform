var edx = edx || {};

(function($) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.EnrollmentInterface = {

        urls: {
            course: '/enrollment/v0/course/',
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
            $.ajax({
                url: this.courseEnrollmentUrl( courseKey ),
                type: 'POST',
                data: {},
                headers: this.headers,
                context: this
            }).always(function() {
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
         * Construct a URL to enroll in a course.
         * @param  {string} courseKey Slash-separated course key.
         * @return {string} The URL to enroll in a course.
         */
        courseEnrollmentUrl: function( courseKey ) {
            return this.urls.course + courseKey;
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
