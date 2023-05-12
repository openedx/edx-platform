(function(define) {
    'use strict';

    define(['backbone'], function(Backbone) {
        // eslint-disable-next-line no-var
        var CourseCohortSettingsModel = Backbone.Model.extend({
            idAttribute: 'id',
            defaults: {
                is_cohorted: false
            }
        });
        return CourseCohortSettingsModel;
    });
// eslint-disable-next-line no-undef
}).call(this, define || RequireJS.define);
