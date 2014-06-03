/* JavaScript for editing operations that can be done on the split test studio view. */
window.SplitTestStudioPreviewView = function (runtime, element) {
    var $element = $(element);

    $element.find('.add-missing-groups-button').click(function () {
        $.post(runtime.handlerUrl(element, 'add_missing_groups'));
    });

    return {};
};
