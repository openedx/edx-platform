/**
 * Model for information about a course.
 */
(function (define) {
    'use strict';
    define(['backbone'], function (Backbone) {
        var CourseInfo = Backbone.Model.extend({
            defaults: {
                id: '',
                name: '',
                category: '',
                org: '',
                run: '',
                course: '',
                uri: '',
                image_url: '',
                start: '',
                end: ''
            }
        });
        return CourseInfo;
    });
}).call(this, define || RequireJS.define);
