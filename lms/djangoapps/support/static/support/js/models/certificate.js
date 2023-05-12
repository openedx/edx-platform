(function(define) {
    'use strict';

    define(['backbone'], function(Backbone) {
        return Backbone.Model.extend({
            defaults: {
                username: null,
                course_key: null,
                type: null,
                status: null,
                grade: null,
                created: null,
                modified: null
            }
        });
    });
// eslint-disable-next-line no-undef
}).call(this, define || RequireJS.define);
