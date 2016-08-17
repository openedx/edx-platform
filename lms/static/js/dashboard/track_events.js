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
        properties.label = $el.data("course-key");

        return properties;
    };

    edx.dashboard.TrackEvents = function() {

         var course_title_link = $(".course-title > a"),
            course_image_link = $(".cover"),
            enter_course_link = $(".enter-course"),
            options_dropdown = $(".wrapper-action-more"),
            course_learn_verified = $(".verified-info"),
            find_courses_btn = $(".btn-find-courses");

        // Emit an event when the "course title link" is clicked.
        window.analytics.trackLink(
            course_title_link,
            "edx.bi.dashboard.course_title.clicked",
            edx.dashboard.generateTrackProperties
        );

        // Emit an event  when the "course image" is clicked.
        window.analytics.trackLink(
            course_image_link,
            "edx.bi.dashboard.course_image.clicked",
            edx.dashboard.generateTrackProperties
        );

        // Emit an event  when the "View Course" button is clicked.
        window.analytics.trackLink(
            enter_course_link,
            "edx.bi.dashboard.enter_course.clicked",
            edx.dashboard.generateTrackProperties
        );

        // Emit an event when the options dropdown is engaged.
        window.analytics.trackLink(
            options_dropdown,
            "edx.bi.dashboard.course_options_dropdown.clicked",
            edx.dashboard.generateTrackProperties
        );

        // Emit an event  when the "Learn about verified" link is clicked.
        window.analytics.trackLink(
            course_learn_verified,
            "edx.bi.dashboard.verified_info_link.clicked",
            edx.dashboard.generateTrackProperties
        );

        // Emit an event  when the "Find Courses" button is clicked.
        window.analytics.trackLink(
            find_courses_btn,
            "edx.bi.dashboard.find_courses_button.clicked",
            {
                category: "dashboard",
                label: null
            }
        );

    };

    $(document).ready(function() {
        edx.dashboard.TrackEvents();
    });
})(jQuery);
