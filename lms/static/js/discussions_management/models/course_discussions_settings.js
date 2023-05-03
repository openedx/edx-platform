(function(define) {
    'use strict';
    define(['backbone'], function(Backbone) {
        var CourseDiscussionsSettingsModel = Backbone.Model.extend({
            idAttribute: 'id',
            defaults: {
                divided_inline_discussions: [],
                divided_course_wide_discussions: [],
                always_divide_inline_discussions: false,
                division_scheme: 'none'
            }
        });
        return CourseDiscussionsSettingsModel;
    });
}).call(this, define || RequireJS.define);
