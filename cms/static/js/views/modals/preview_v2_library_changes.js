/**
 * The PreviewLibraryChangesModal is a Backbone view that shows an iframe in a
 * modal window. The iframe embeds a view from the Authoring MFE that allows
 * authors to preview the new version of a library-sourced XBlock, and decide
 * whether to accept ("sync") or reject ("ignore") the changes.
 */
define(['jquery', 'underscore', 'gettext', 'js/views/modals/base_modal',
    'js/views/utils/xblock_utils'],
function($, _, gettext, BaseModal, XBlockViewUtils) {
    'use strict';

    var PreviewLibraryChangesModal = BaseModal.extend({
        events: _.extend({}, BaseModal.prototype.events, {
            'click .action-accept': 'acceptChanges',
            'click .action-ignore': 'ignoreChanges',
        }),

        options: $.extend({}, BaseModal.prototype.options, {
            modalName: 'preview-lib-changes',
            modalSize: 'med',
            view: 'studio_view',
            viewSpecificClasses: 'modal-lib-preview confirm',
            // Translators: "title" is the name of the current component being edited.
            titleFormat: gettext('Preview changes to: {title}'),
            addPrimaryActionButton: false,
        }),

        initialize: function() {
            BaseModal.prototype.initialize.call(this);
            // this.template = this.loadTemplate('edit-xblock-modal');
            // this.editorModeButtonTemplate = this.loadTemplate('editor-mode-button');
        },

        /**
         * Adds the action buttons to the modal.
         */
        addActionButtons: function() {
            this.addActionButton('accept', gettext('Accept changes'), true);
            this.addActionButton('ignore', gettext('Ignore changes'));
            this.addActionButton('cancel', gettext('Cancel'));
        },

        /**
         * Show an edit modal for the specified xblock
         * @param xblockElement The element that contains the xblock to be edited.
         * @param rootXBlockInfo An XBlockInfo model that describes the root xblock on the page.
         * @param refreshFunction A function to refresh the block after it has been updated
         */
        showPreviewFor: function(xblockElement, rootXBlockInfo, refreshFunction) {
            this.xblockElement = xblockElement;
            this.xblockInfo = XBlockViewUtils.findXBlockInfo(xblockElement, rootXBlockInfo);
            this.courseAuthoringMfeUrl = rootXBlockInfo.attributes.course_authoring_url;
            const headerElement = xblockElement.find('.xblock-header-primary');
            this.upstreamBlockId = headerElement.data('upstream-ref');
            this.upstreamBlockVersionSynced = headerElement.data('version-synced');
            // this.options.modalType = this.xblockInfo.get('category');
            this.refreshFunction = refreshFunction;

            this.render();
            this.show();
        },

        getContentHtml: function() {
            return `
                <iframe src="${this.courseAuthoringMfeUrl}/legacy/preview-changes/${this.upstreamBlockId}?old=${this.upstreamBlockVersionSynced}">
            `;
        },

        getTitle: function() {
            var displayName = this.xblockInfo.get('display_name');
            if (!displayName) {
                if (this.xblockInfo.isVertical()) {
                    displayName = gettext('Unit');
                } else {
                    displayName = gettext('Component');
                }
            }
            return edx.StringUtils.interpolate(
                this.options.titleFormat, {
                    title: displayName
                }
            );
        },

        acceptChanges: function(event) {
            event.preventDefault();
        },

        ignoreChanges: function(event) {
            event.preventDefault();
            if (confirm(gettext('Are you sure you want to ignore these changes?'))) {
                // TODO
            }
        },
    });

    return PreviewLibraryChangesModal;
});
