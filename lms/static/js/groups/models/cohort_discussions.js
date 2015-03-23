var edx = edx || {};

(function(Backbone) {
    'use strict';

    edx.groups = edx.groups || {};

    edx.groups.DiscussionTopicsSettingsModel = Backbone.Model.extend({
        defaults: {
            course_wide_discussions: {},
            inline_discussions: {}
        }
    });
}).call(this, Backbone);
