/* JavaScript for editing operations that can be done on LibraryContentXBlock */
window.LibraryContentAuthorView = function (runtime, element) {
    $(element).find('.library-update-btn').on('click', function(e) {
        e.preventDefault();
        // Update the XBlock with the latest matching content from the library:
        runtime.notify('save', {
            state: 'start',
            element: element,
            message: gettext('Updating with latest library content')
        });
        $.post(runtime.handlerUrl(element, 'refresh_children')).done(function() {
            runtime.notify('save', {
                state: 'end',
                element: element
            });
            // runtime.refreshXBlock(element);
            // The above does not work, because this XBlock's runtime has no reference
            // to the page (XBlockContainerPage). Only the Vertical XBlock's runtime has
            // a reference to the page, and we have no way of getting a reference to it.
            // So instead we:
            location.reload();
        });
    });
};
