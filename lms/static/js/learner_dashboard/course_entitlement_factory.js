(function(define) {
    'use strict';

    define([
        'js/learner_dashboard/views/course_entitlement_view'
    ],
    function(EntitlementView) {
        return function(options) {
            return new EntitlementView(options);
        };
    });
}).call(this, define || RequireJS.define);
