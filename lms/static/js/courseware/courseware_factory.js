(function(define) {
    'use strict';

    define([
        'jquery',
        'logger',
        'js/bookmarks/views/bookmarks_list_button'
    ],
        function($, Logger, BookmarksListButton) {
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

                // 2. instantiating this button attaches events to all buttons in the courseware.
                new BookmarksListButton();  // eslint-disable-line no-new
            };
        }
    );
}).call(this, define || RequireJS.define);
