(function(define) {
    'use strict';

    define([
        'jquery',
        'js/student_account/views/AccessView'
    ],
    function($, AccessView) {
        return function(options) {
            // eslint-disable-next-line no-var
            var $logistrationElement = $('#login-and-registration-container');

            /* eslint-disable-next-line no-new, no-undef */
            new AccessView(_.extend(options, {el: $logistrationElement}));
        };
    }
    );
// eslint-disable-next-line no-undef
}).call(this, define || RequireJS.define);
