// eslint-disable-next-line no-undef
define([
    'js/views/pages/course_outline', 'js/models/xblock_outline_info'
], function(CourseOutlinePage, XBlockOutlineInfo) {
    'use strict';

    return function(XBlockOutlineInfoJson, initialStateJson) {
        // eslint-disable-next-line no-var
        var courseXBlock = new XBlockOutlineInfo(XBlockOutlineInfoJson, {parse: true}),
            view = new CourseOutlinePage({
                el: $('#content'),
                model: courseXBlock,
                initialState: initialStateJson
            });
        view.render();
    };
});
