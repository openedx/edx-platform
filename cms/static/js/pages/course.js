define(
    ['js/models/course'],
    function(ContextCourse) {
        window.course = new ContextCourse(window.pageFactoryArguments.ContextCourse);
    }
);
