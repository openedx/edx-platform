/**
 * Track interaction with the student dashboard..
 */

var edx = edx || {};

(function ($) {
    'use strict';

    edx.dashboard = edx.dashboard || {};

    // Generate the properties object to be passed along with business intelligence events.
    edx.dashboard.generateTrackProperties = function(element){
        var $el = $(element),
            properties = {};

        properties.category = 'dashboard';
        properties.label = $el.data('course-key');

        return properties;
    };

    // Generate object to be passed with programs events
    edx.dashboard.generateProgramProperties = function(element) {
        var $el = $(element);

        return {
            category: 'dashboard',
            course_id: $el.closest('.course-container').find('.info-course-id').html(),
            program_id: $el.data('program-id')
        };
    };

    edx.dashboard.trackEvents = function() {
        var $courseTitleLink = $('.course-title > a'),
            $courseImageLink = $('.cover'),
            $enterCourseLink = $('.enter-course'),
            $optionsDropdown = $('.wrapper-action-more'),
            $courseLearnVerified = $('.verified-info'),
            $findCoursesBtn = $('.btn-find-courses'),
            $xseriesBtn = $('.xseries-action .btn');

        // Emit an event when the 'course title link' is clicked.
        window.analytics.trackLink(
            $courseTitleLink,
            'edx.bi.dashboard.course_title.clicked',
            edx.dashboard.generateTrackProperties
        );

        // Emit an event  when the 'course image' is clicked.
        window.analytics.trackLink(
            $courseImageLink,
            'edx.bi.dashboard.course_image.clicked',
            edx.dashboard.generateTrackProperties
        );

        // Emit an event  when the 'View Course' button is clicked.
        window.analytics.trackLink(
            $enterCourseLink,
            'edx.bi.dashboard.enter_course.clicked',
            edx.dashboard.generateTrackProperties
        );

        // Emit an event when the options dropdown is engaged.
        window.analytics.trackLink(
            $optionsDropdown,
            'edx.bi.dashboard.course_options_dropdown.clicked',
            edx.dashboard.generateTrackProperties
        );

        // Emit an event  when the 'Learn about verified' link is clicked.
        window.analytics.trackLink(
            $courseLearnVerified,
            'edx.bi.dashboard.verified_info_link.clicked',
            edx.dashboard.generateTrackProperties
        );

        // Emit an event  when the 'Find Courses' button is clicked.
        window.analytics.trackLink(
            $findCoursesBtn,
            'edx.bi.dashboard.find_courses_button.clicked',
            {
                category: 'dashboard',
                label: null
            }
        );

        // Emit an event when the 'View XSeries Details' button is clicked
        window.analytics.trackLink(
            $xseriesBtn,
            'edx.bi.dashboard.xseries_cta_message.clicked',
            edx.dashboard.generateProgramProperties
        );
    };

    edx.dashboard.xseriesTrackMessages = function() {
        $('.xseries-action .btn').each(function(i, element) {
            var data = edx.dashboard.generateProgramProperties($(element));

            window.analytics.track( 'edx.bi.dashboard.xseries_cta_message.viewed', data );
        });
    };

    $(document).ready(function() {
        edx.dashboard.trackEvents();
        edx.dashboard.xseriesTrackMessages();
    });
})(jQuery);
