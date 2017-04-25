(function(define) {
    'use strict';

    define([
        'jquery',
        'logger'
    ],
        function($, Logger) {
            return function() {
                // This function performs all actions common to all courseware.
                // 1. adding an event to all link clicks.
                $('a:not([href^="#"])').click(function(event) {
                    Logger.log(
                        'edx.ui.lms.link_clicked',
                        {
                            current_url: window.location.href,
                            target_url: event.currentTarget.href
                        });
                });
            };
        }
    );
}).call(this, define || RequireJS.define);
