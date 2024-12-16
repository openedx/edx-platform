/**
 * Provides utilities to open and close the library content picker.
 * This is for adding multiple components to a Problem Bank (for randomization).
 *
 * Compare cms/static/js/views/components/add_library_content.js which uses
 * a single-select modal to add one component to a course (non-randomized).
 */
define(['jquery', 'underscore', 'gettext', 'js/views/modals/base_modal'],
function($, _, gettext, BaseModal) {
    'use strict';

    var SelectV2LibraryContent = BaseModal.extend({
        options: $.extend({}, BaseModal.prototype.options, {
            modalName: 'add-components-from-library',
            modalSize: 'lg',
            view: 'studio_view',
            viewSpecificClasses: 'modal-add-component-picker confirm',
            titleFormat: gettext('Add library content'),
            addPrimaryActionButton: false,
        }),

        events: {
            'click .action-add': 'addSelectedComponents',
            'click .action-cancel': 'cancel',
        },

        initialize: function() {
            BaseModal.prototype.initialize.call(this);
            this.selections = [];
            // Add event listen to close picker when the iframe tells us to
            const handleMessage = (event) => {
                if (event.data?.type === 'pickerSelectionChanged') {
                    this.selections = event.data.selections;
                    if (this.selections.length > 0) {
                        this.enableActionButton('add');
                    } else {
                        this.disableActionButton('add');
                    }
                }
                if (event.data?.type === 'addSelectedComponentsToBank') {
                    this.selections = event.data.payload.selectedComponents;
                    this.callback(this.selections);
                }
            };
            this.messageListener = window.addEventListener("message", handleMessage);
            this.cleanupListener = () => { window.removeEventListener("message", handleMessage) };
        },

        hide: function() {
            BaseModal.prototype.hide.call(this);
            this.cleanupListener();
        },

        /**
         * Adds the action buttons to the modal.
         */
        addActionButtons: function() {
            this.addActionButton('add', gettext('Add selected components'), true);
            this.addActionButton('cancel', gettext('Cancel'));
            this.disableActionButton('add');
        },

        /** Handler when the user clicks the "Add Selected Components" primary button */
        addSelectedComponents: function(event) {
            if (event) {
                event.preventDefault();
                event.stopPropagation(); // Make sure parent modals don't see the click
            }
            this.hide();
            this.callback(this.selections);
        },

        /**
         * Show a component picker modal from library.
         * @param contentPickerUrl Url for component picker
         * @param callback A function to call with the selected block(s)
         * @param isIframeEmbed Boolean indicating if the unit is displayed inside an iframe
         */
        showComponentPicker: function(contentPickerUrl, callback, isIframeEmbed) {
            this.contentPickerUrl = contentPickerUrl;
            this.callback = callback;
            if (isIframeEmbed) {
                window.parent.postMessage(
                    {
                        type: 'showMultipleComponentPicker',
                        payload: {}
                    }, document.referrer
                );
                return true;
            }

            this.render();
            this.show();
        },

        getContentHtml: function() {
            return `<iframe src="${this.contentPickerUrl}" onload="this.contentWindow.focus()" frameborder="0" style="width: 100%; height: 100%;"/>`;
        },
    });

    return SelectV2LibraryContent;
});
