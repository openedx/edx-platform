/* Javascript for the Acid XBlock. */
function SplitTestStudentView(runtime, element) {
    $.post(runtime.handlerUrl(element, 'log_child_render'));
    return {};
}
