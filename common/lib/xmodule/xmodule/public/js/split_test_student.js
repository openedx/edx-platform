/* Javascript for the Split Test XBlock. */
function SplitTestStudentView(runtime, element) {
    $.post(runtime.handlerUrl(element, 'log_child_render'));
    return {};
}
