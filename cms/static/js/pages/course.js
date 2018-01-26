define(
    ['js/models/course'],
    function(ContextCourse) {
        'use strict';
        window.course = new ContextCourse(window.pageFactoryArguments.ContextCourse[0]);
    }
);

