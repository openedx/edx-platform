(function(define) {
    'use strict';
    define(['backbone'], function(Backbone) {
        return Backbone.Model.extend({
            defaults: {
                fileName: null,
                fileToken: null
            }
        });
    });
}).call(this, define || RequireJS.define);
