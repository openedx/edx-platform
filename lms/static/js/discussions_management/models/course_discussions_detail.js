(function(define) {
    'use strict';
    define(['backbone'], function(Backbone) {
        var CourseDiscussionTopicDetailsModel = Backbone.Model.extend({
            defaults: {
                course_wide_discussions: {},
                inline_discussions: {}
            }
        });
        return CourseDiscussionTopicDetailsModel;
    });
}).call(this, define || RequireJS.define);
