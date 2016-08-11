/* Javascript for the Split Test XBlock. */
window.SplitTestStudentView = function(runtime, element) {
    'use strict';
    $.post(runtime.handlerUrl(element, 'log_child_render'));
    return {};
};
