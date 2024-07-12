(function(define) {
    'use strict';

    define([
        'jquery',
        'js/student_account/views/AccessView'
    ],
    function($, AccessView) {
        return function(options) {
            var $logistrationElement = $('#login-and-registration-container');

            // eslint-disable-next-line no-new
            new AccessView(_.extend(options, {el: $logistrationElement}));
        };
    }
    );
}).call(this, define || RequireJS.define);
