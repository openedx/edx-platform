define([
    'jquery',
    'js/certificates/views/add_course_mode'
],
function($, CourseModeHandler) {
    'use strict';
    return function(enableCourseModeCreation, courseModeCreationUrl, courseId) {
        // Execute the page object's rendering workflow
        new CourseModeHandler({
            enableCourseModeCreation: enableCourseModeCreation,
            courseModeCreationUrl: courseModeCreationUrl,
            courseId: courseId
        }).show();
    };
});
