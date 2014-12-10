define(['js/models/course'], function(Course) {
    'use strict';
    return function (courseInfo) {
        window.course = new Course(courseInfo);
    }
});
