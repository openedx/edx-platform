/**
* Module for emitting Course Sharing Events.
*/
(function(define) {
    'use strict';

    define(['jquery', 'logger'], function($, Logger) {
        return function(courseId) {
            $(".action-facebook[data-course-id='" + courseId + "']").on('click', function() {
                // Emit an event telling that the Facebook share link was clicked.
                Logger.log('edx.course.share_clicked', {
                    course_id: courseId,
                    social_media_site: 'facebook',
                    location: 'dashboard'
                });
            });

            $(".action-twitter[data-course-id='" + courseId + "']").on('click', function() {
                // Emit an event telling that the Twitter share link was clicked.
                Logger.log('edx.course.share_clicked', {
                    course_id: courseId,
                    social_media_site: 'twitter',
                    location: 'dashboard'
                });
            });
        };
    });
}).call(this, define || RequireJS.define);
