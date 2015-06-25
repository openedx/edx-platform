var edx = edx || {};

(function(Backbone) {
    'use strict';

    edx.groups = edx.groups || {};

    edx.groups.CourseCohortSettingsModel = Backbone.Model.extend({
        idAttribute: 'id',
        defaults: {
            is_cohorted: false,
            cohorted_inline_discussions: [],
            cohorted_course_wide_discussions:[],
            always_cohort_inline_discussions: true
        }
    });
}).call(this, Backbone);
