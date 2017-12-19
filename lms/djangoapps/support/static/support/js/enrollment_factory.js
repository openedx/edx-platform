(function(define) {
    'use strict';

    define([
        'underscore',
        'support/js/views/enrollment'
    ], function(_, EnrollmentView) {
        return function(options) {
            options = _.extend({el: '.enrollment-content'}, options);
            return new EnrollmentView(options).render();
        };
    });
}).call(this, define || RequireJS.define);
