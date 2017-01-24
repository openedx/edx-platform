(function(define) {
    'use strict';
    define(['backbone'], function(Backbone) {
        var CourseCohortSettingsModel = Backbone.Model.extend({
            idAttribute: 'id',
            defaults: {
                is_cohorted: false,
                cohorted_inline_discussions: [],
                cohorted_course_wide_discussions: [],
                always_cohort_inline_discussions: true
            }
        });
        return CourseCohortSettingsModel;
    });
}).call(this, define || RequireJS.define);
