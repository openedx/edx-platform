/**
 * Provides utilities to open and close the library content picker.
 * This is for adding a single, selected, non-randomized component (XBlock)
 * from the library into the course. It achieves the same effect as copy-pasting
 * the block from a library into the course. The block will remain synced with
 * the "upstream" library version.
 *
 * Compare cms/static/js/views/modals/select_v2_library_content.js which uses
 * a multi-select modal to add component(s) to a Problem Bank (for
 * randomization).
 */
define(['jquery', 'underscore', 'gettext', 'js/views/modals/base_modal'],
function($, _, gettext, BaseModal) {
    'use strict';

    var AddLibraryContent = BaseModal.extend({
        options: $.extend({}, BaseModal.prototype.options, {
            modalName: 'add-component-from-library',
            modalSize: 'lg',
            view: 'studio_view',
            viewSpecificClasses: 'modal-add-component-picker confirm',
            // Translators: "title" is the name of the current component being edited.
            titleFormat: gettext('Add library content'),
            addPrimaryActionButton: false,
            showEditorModeButtons: false,
        }),

        initialize: function() {
            BaseModal.prototype.initialize.call(this);
            // Add event listen to close picker when the iframe tells us to
            const handleMessage = (event) => {
                if (event.data?.type === 'pickerComponentSelected') {
                    var requestData = {
                        library_content_key: event.data.usageKey,
                        category: event.data.category,
                    }
                    this.refreshFunction(requestData);
                    this.hide();
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
            this.addActionButton('cancel', gettext('Cancel'));
        },

        /**
         * Show a component picker modal from library.
         * @param contentPickerUrl Url for component picker
         * @param refreshFunction A function to refresh the block after it has been updated
         */
        showComponentPicker: function(contentPickerUrl, refreshFunction) {
            this.contentPickerUrl = contentPickerUrl;
            this.refreshFunction = refreshFunction;

            this.render();
            this.show();
        },

        getContentHtml: function() {
            return `<iframe src="${this.contentPickerUrl}" onload="this.contentWindow.focus()" frameborder="0" style="width: 100%; height: 100%;"/>`;
        },
    });

    return AddLibraryContent;
});
