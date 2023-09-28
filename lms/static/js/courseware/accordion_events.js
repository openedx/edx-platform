(function(define) {
    'use strict';

    define(['jquery', 'logger'], function($, Logger) {
        return function() {
            $('.accordion-nav').click(function(event) {
                Logger.log(
                    'edx.ui.lms.outline.selected',
                    {
                        current_url: window.location.href,
                        target_url: event.currentTarget.href,
                        target_name: $(this).find('p.accordion-display-name').text(),
                        widget_placement: 'accordion'
                    });
            });
        };
    });
}).call(this, define || RequireJS.define);
