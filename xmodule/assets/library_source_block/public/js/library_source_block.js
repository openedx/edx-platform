/* JavaScript for allowing editing options on LibrarySourceBlock's studio view */
window.LibrarySourceBlockStudioView = function(runtime, element) {
    'use strict';
    var self = this;

    $('#library-sourced-block-picker', element).on('selected-xblocks', function(e, params) {
        self.sourceBlockIds = params.sourceBlockIds;
    });

    $('#library-sourced-block-picker', element).on('error', function(e, params) {
        runtime.notify('error', {title: gettext(params.title), message: params.message});
    });

    $('.save-button', element).on('click', function(e) {
        e.preventDefault();
        var url = $(e.target).data('submit-url');
        var data = {
            values: {
                source_block_ids: self.sourceBlockIds
            },
            defaults: ['display_name']
        };

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

    $('.cancel-button', element).on('click', function(e) {
        e.preventDefault();
        runtime.notify('cancel', {});
    });
};
