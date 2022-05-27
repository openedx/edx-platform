(function($) {
    'use strict';

    function StructuredTagsView(runtime, element) {
        var $element = $(element);
        var saveTagsInProgress = false;
        // we need studio runtime to get handler capable of saving xblock data
        var studioRuntime = new window.StudioRuntime.v1();

        $($element).find('.save_tags').click(function(e) {
            var dataToPost = {};
            if (!saveTagsInProgress) {
                saveTagsInProgress = true;

                $element.find('select').each(function() {
                    dataToPost[$(this).attr('name')] = $(this).val();
                });

                e.preventDefault();
                runtime.notify('save', {
                    state: 'start',
                    element: element,
                    message: gettext('Updating Tags')
                });

                $.ajax({
                    type: 'POST',
                    url: studioRuntime.handlerUrl(element, 'save_tags'),
                    data: JSON.stringify(dataToPost),
                    dataType: 'json',
                    contentType: 'application/json; charset=utf-8'
                }).always(function() {
                    runtime.notify('save', {
                        state: 'end',
                        element: element
                    });
                    saveTagsInProgress = false;
                });
            }
        });
    }

    function initializeStructuredTags(runtime, element) {
        return new StructuredTagsView(runtime, element);
    }

    window.StructuredTagsInit = initializeStructuredTags;
}($));
