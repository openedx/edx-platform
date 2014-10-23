function DiscussionEditBlock(runtime, element) {
    $('.save-button').bind('click', function() {
        var data = {
            'display_name': $('#display-name').val(),
            'discussion_category': $('#discussion-category').val(),
            'discussion_target': $('#discussion-target').val()
        };
        var handlerUrl = runtime.handlerUrl(element, 'studio_submit');
        $.post(handlerUrl, JSON.stringify(data)).complete(function() {
            window.location.reload(false);
        });
    });

    $('.cancel-button').bind('click', function() {
        runtime.notify('cancel', {});
    });
}
