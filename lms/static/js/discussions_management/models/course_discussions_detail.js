(function(define) {
    'use strict';

    define(['backbone'], function(Backbone) {
        // eslint-disable-next-line no-var
        var CourseDiscussionTopicDetailsModel = Backbone.Model.extend({
            defaults: {
                course_wide_discussions: {},
                inline_discussions: {}
            }
        });
        return CourseDiscussionTopicDetailsModel;
    });
// eslint-disable-next-line no-undef
}).call(this, define || RequireJS.define);
