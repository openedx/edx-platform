(function(define) {
    'use strict';
    define(['backbone'], function(Backbone) {
        var DiscussionTopicsSettingsModel = Backbone.Model.extend({
            defaults: {
                course_wide_discussions: {},
                inline_discussions: {}
            }
        });
        return DiscussionTopicsSettingsModel;
    });
}).call(this, define || RequireJS.define);
