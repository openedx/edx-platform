(function($) {
    'use strict';

    function StructuredTagsView(runtime, element) {

        var $element = $(element);

        $element.find("select").each(function() {
            var loader = this;
            var sts = $(this).attr('structured-tags-select-init');

            if (typeof sts === typeof undefined || sts === false) {
                $(this).attr('structured-tags-select-init', 1);
                $(this).change(function(e) {
                    e.preventDefault();
                    var selectedKey = $(loader).find('option:selected').val();
                    runtime.notify('save', {
                        state: 'start',
                        element: element,
                        message: gettext('Updating Tags')
                    });
                    $.post(runtime.handlerUrl(element, 'save_tags'), {
                        'tag': $(loader).attr('name') + ':' + selectedKey
                    }).done(function() {
                        runtime.notify('save', {
                            state: 'end',
                            element: element
                        });
                    });
                });
            }
        });
    }

    function initializeStructuredTags(runtime, element) {
        return new StructuredTagsView(runtime, element);
    }

    window.StructuredTagsInit = initializeStructuredTags;
})($);
