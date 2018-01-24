(function(define) {
    'use strict';

    define(
        ['js/models/course'],
        function(ContextCourse) {
            window.course = new ContextCourse(window.pageFactoryArguments.ContextCourse[0]);
        }
    );
}).call(this, define || RequireJS.define);
