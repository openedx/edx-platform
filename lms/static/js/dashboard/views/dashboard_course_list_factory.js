;(function (define) {
    'use strict';

    define(['js/dashboard/views/course_list_tabbed_view'],
        function (CourseListTabbedView) {
            return function (currentCourses, archivedCourses, templateSettings) {
                new CourseListTabbedView(currentCourses, archivedCourses, templateSettings).render();
            };
        });
}).call(this, define || RequireJS.define);
