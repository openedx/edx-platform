/* JavaScript for special editing operations that can be done on LibraryContentXBlock */
window.LibraryContentAuthorView = function(runtime, element) {
    'use strict';
    var $element = $(element);
    var usage_id = $element.data('usage-id');
    // The "Update Now" button is not a child of 'element', as it is in the validation message area
    // But it is still inside this xblock's wrapper element, which we can easily find:
    var $wrapper = $element.parents('*[data-locator="' + usage_id + '"]');

    $wrapper.on('click', '.library-update-btn', function(e) {
        e.preventDefault();
        // Update the XBlock with the latest matching content from the library:
        runtime.notify('save', {
            state: 'start',
            element: element,
            message: gettext('Updating with latest library content')
        });
        $.post(runtime.handlerUrl(element, 'upgrade_and_sync')).done(function() {
            runtime.notify('save', {
                state: 'end',
                element: element
            });
            if ($element.closest('.wrapper-xblock').is(':not(.level-page)')) {
                // We are on a course unit page. The notify('save') should refresh this block,
                // but that is only working on the container page view of this block.
                // Why? On the unit page, this XBlock's runtime has no reference to the
                // XBlockContainerPage - only the top-level XBlock (a vertical) runtime does.
                // But unfortunately there is no way to get a reference to our parent block's
                // JS 'runtime' object. So instead we must refresh the whole page:
                location.reload();
            }
        });
    });
    // Hide loader and show element when update task finished.
    var $loader = $wrapper.find('.ui-loading');
    var $xblockHeader = $wrapper.find('.xblock-header');
    if (!$loader.hasClass('is-hidden')) {
        var timer = setInterval(function() {
            $.get(runtime.handlerUrl(element, 'children_are_syncing'), function( data ) {
                if (data !== true) {
                    $loader.addClass('is-hidden');
                    $xblockHeader.removeClass('is-hidden');
                    clearInterval(timer);
                    runtime.notify('save', {
                        state: 'end',
                        element: element
                    });
                }
            })
        }, 1000);
    }
};
