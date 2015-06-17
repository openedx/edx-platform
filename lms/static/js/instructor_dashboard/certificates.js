var edx = edx || {};

(function( $, gettext ) {
    'use strict';

    edx.instructor_dashboard = edx.instructor_dashboard || {};
    edx.instructor_dashboard.certificates = {};

    $(function() {
        /**
         * Show a confirmation message before letting staff members
         * enable/disable self-generated certificates for a course.
         */
        $('#enable-certificates-form').on('submit', function( event ) {
            var isEnabled = $('#certificates-enabled').val() === 'true',
                confirmMessage = '';

            if ( isEnabled ) {
                confirmMessage = gettext('Allow students to generate certificates for this course?');
            } else {
                confirmMessage = gettext('Prevent students from generating certificates in this course?');
            }

            if ( !confirm( confirmMessage ) ) {
                event.preventDefault();
            }
        });

        /**
         * Refresh the status for example certificate generation
         * by reloading the instructor dashboard.
         */
        $('#refresh-example-certificate-status').on('click', function() {
            window.location.reload();
        });
    });
})( $, gettext );
