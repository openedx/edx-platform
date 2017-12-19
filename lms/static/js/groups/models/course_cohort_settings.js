(function(define) {
    'use strict';
    define(['backbone'], function(Backbone) {
        var CourseCohortSettingsModel = Backbone.Model.extend({
            idAttribute: 'id',
            defaults: {
                is_cohorted: false
            }
        });
        return CourseCohortSettingsModel;
    });
}).call(this, define || RequireJS.define);
