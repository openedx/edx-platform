/* globals window, $$course_id, DiscussionUtil */
function DiscussionCourseBlock(runtime, element) {
    'use strict';
    var hasPushState = window.history && window.history.pushState ? true : false;
    DiscussionUtil.force_async = true;

    // Restart the Backbone router to use the discussion root when
    // links inside this component are clicked.
    if (Backbone.History.started) {
        Backbone.history.stop();
    }
    Backbone.history.start({
        pushState: hasPushState,
        root: "/courses/" + $$course_id + "/discussion/"
    });
}
