var edx = edx || {};

(function($, gettext, _) {
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


        /**
         * Start generating certificates for all students.
         */
        var $section = $("section#certificates");
        $section.on('click', '#btn-start-generating-certificates', function(event) {
            if ( !confirm( gettext('Start generating certificates for all students in this course?') ) ) {
                event.preventDefault();
                return;
            }

            var $btn_generating_certs = $(this),$certificate_generation_status = $('.certificate-generation-status');
            var url = $btn_generating_certs.data('endpoint');
            $.ajax({
                type: "POST",
                url: url,
                success: function (data) {
                    $btn_generating_certs.attr('disabled','disabled');
                    $certificate_generation_status.text(data.message);
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    $certificate_generation_status.text(gettext('Error while generating certificates. Please try again.'));
                }
            });
        });
    });

    var Certificates = (function() {
        function Certificates($section) {
            $section.data('wrapper', this);
            this.instructor_tasks = new window.InstructorDashboard.util.PendingInstructorTasks($section);
        }

        Certificates.prototype.onClickTitle = function() {
            return this.instructor_tasks.task_poller.start();
        };

        Certificates.prototype.onExit = function() {
            return this.instructor_tasks.task_poller.stop();
        };
        return Certificates;
    })();

    _.defaults(window, {
        InstructorDashboard: {}
    });

    _.defaults(window.InstructorDashboard, {
        sections: {}
    });

    _.defaults(window.InstructorDashboard.sections, {
        Certificates: Certificates
    });

})($, gettext, _);
