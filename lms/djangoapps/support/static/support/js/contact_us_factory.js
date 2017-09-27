(function(define) {
    'use strict';

    define([
        'underscore',
        'support/js/views/contact_us'
    ], function(_, ContactUsView) {
        return function(options) {
            options = _.extend({el: '.contact-us-wrapper'}, options);
            return new ContactUsView(options).render();
        };
    });
}).call(this, define || RequireJS.define);
