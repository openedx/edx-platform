(function(define) {
    'use strict';

    define(['backbone'], function(Backbone) {
        // eslint-disable-next-line no-var
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
// eslint-disable-next-line no-undef
}).call(this, define || RequireJS.define);
