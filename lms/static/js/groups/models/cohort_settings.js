var edx = edx || {};

(function(Backbone) {
    'use strict';

    edx.groups = edx.groups || {};

    edx.groups.CohortSettingsModel = Backbone.Model.extend({
        idAttribute: 'id',
        defaults: {
            is_cohorted: false,
            cohorted_discussions: [],
            always_cohort_inline_discussions: true
        }
    });
}).call(this, Backbone);
