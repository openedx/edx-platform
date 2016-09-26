(function(define) {
    'use strict';
    define(['backbone'], function(Backbone) {
        return Backbone.Model.extend({
            defaults: {
                location: '',
                display_name: '',
                start: null,
                due: null,
                category: '',
                hidden: false,
                children: []
            }
        });
    });
}).call(this, define || RequireJS.define);
