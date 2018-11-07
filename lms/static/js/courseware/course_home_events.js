(function(define) {
    'use strict';

    define(['jquery', 'logger'], function($, Logger) {
        return function() {
            $('.last-accessed-link').on('click', function(event) {
                Logger.log('edx.course.home.resume_course.clicked', {
                    url: event.currentTarget.href
                });
            });
            $('.date-summary-verified-upgrade-deadline .date-summary-link').on('click', function() {
                Logger.log('edx.course.home.upgrade_verified.clicked', {location: 'sidebar'});
            });
            $('.upgrade-banner-button').on('click', function() {
                Logger.log('edx.course.home.upgrade_verified.clicked', {location: 'notification'});
            });
            $('.view-verified-info').on('click', function() {
                Logger.log('edx.course.home.learn_about_verified.clicked', {location: 'notification'});
            });
        };
    });
}).call(this, define || RequireJS.define);
