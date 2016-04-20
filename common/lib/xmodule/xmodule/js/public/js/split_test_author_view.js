/* JavaScript for editing operations that can be done on the split test author view. */
window.SplitTestAuthorView = function (runtime, element) {
    var $element = $(element);
    var splitTestLocator = $element.closest('.studio-xblock-wrapper').data('locator');

    runtime.listenTo("add-missing-groups", function (parentLocator) {
        if (splitTestLocator === parentLocator) {
            runtime.notify('save', {
                state: 'start',
                element: element,
                message: gettext('Creating missing groups')
            });
            $.post(runtime.handlerUrl(element, 'add_missing_groups')).done(function() {
                runtime.notify('save', {
                    state: 'end',
                    element: element
                });
            });
        }
    });

    // Listen to delete events so that the view can refresh when the last inactive group is removed.
    runtime.listenTo('deleted-child', function(parentLocator) {
        var inactiveGroups = $element.find('.is-inactive .studio-xblock-wrapper');
        if (splitTestLocator === parentLocator && inactiveGroups.length === 0) {
            runtime.refreshXBlock($element);
        }
    });

    return {};
};
