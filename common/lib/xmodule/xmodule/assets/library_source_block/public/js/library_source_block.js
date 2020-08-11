/* JavaScript for allowing editing options on LibrarySourceBlock's author view */
window.LibrarySourceBlockAuthorView = function(runtime, element) {
    'use strict';
    var $element = $(element);

    $element.on('click', '.save-btn', function(e) {
        var url = $(e.target).data('submit-url');
        var data = {
            values: {
                source_block_id: $element.find('input').val()
            },
            defaults: ['display_name']
        };
        e.preventDefault();

        runtime.notify('save', {
            state: 'start',
            message: gettext('Saving'),
            element: element
        });
        $.ajax({
            type: 'POST',
            url: url,
            data: JSON.stringify(data),
            global: false // Disable error handling that conflicts with studio's notify('save') and notify('cancel')
        }).done(function() {
            runtime.notify('save', {
                state: 'end',
                element: element
            });
        }).fail(function(jqXHR) {
            var message = gettext('This may be happening because of an error with our server or your internet connection. Try refreshing the page or making sure you are online.');  // eslint-disable-line max-len
            if (jqXHR.responseText) { // Is there a more specific error message we can show?
                try {
                    message = JSON.parse(jqXHR.responseText).error;
                    if (typeof message === 'object' && message.messages) {
                        // e.g. {"error": {"messages": [{"text": "Unknown user 'bob'!", "type": "error"}, ...]}} etc.
                        message = $.map(message.messages, function(msg) { return msg.text; }).join(', ');
                    }
                } catch (error) { message = jqXHR.responseText.substr(0, 300); }
            }
            runtime.notify('error', {title: gettext('Unable to update settings'), message: message});
        });
    });
};
