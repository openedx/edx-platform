(function(define) {
    'use strict';
    define(['backbone'], function(Backbone) {
        return Backbone.Model.extend({
            defaults: {
                email: null,
                subject: null,
                message: null
            }
        });
    });
}).call(this, define || RequireJS.define);
