(function(define) {
    'use strict';

    define([
        'js/learner_dashboard/views/unenroll_view'
    ],
    function(UnenrollView) {
        return function(options) {
            var Unenroll = new UnenrollView(options);
            return Unenroll;
        };
    });
}).call(this, define || RequireJS.define);
