(function(define) {
    'use strict';

    define([
        'js/learner_dashboard/views/entitlement_unenrollment_view'
    ],
    function(EntitlementUnenrollmentView) {
        return function(options) {
            return new EntitlementUnenrollmentView(options);
        };
    });
}).call(this, define || RequireJS.define);
