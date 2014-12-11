/**
 * The VisibilityModal is a Backbone view that shows the visibility settings for
 * an xblock.
 */
define(["jquery", "underscore", "gettext", "js/views/modals/base_modal", "js/views/utils/view_utils",
    "js/models/xblock_info", "js/views/xblock_editor"],
    function($, _, gettext, BaseModal, ViewUtils, XBlockInfo, XBlockEditorView) {
        "strict mode";
        var VisibilityModal = BaseModal.extend({
            events : {
                "click .action-save": "save"
            },

            options: $.extend({}, BaseModal.prototype.options, {
                modalName: 'xblock-visibility',
                addSaveButton: true
            }),

            initialize: function() {
                BaseModal.prototype.initialize.call(this);
                this.events = _.extend({}, BaseModal.prototype.events, this.events);
                this.template = this.loadTemplate('visibility-modal');
                this.editorModeButtonTemplate = this.loadTemplate('editor-mode-button');
            },

            getContentHtml: function() {
                return this.template({
                    xblockInfo: this.xblockInfo,
                    containerInfo: this.containerInfo
                });
            },

            /**
             * Show an edit modal for the specified xblock
             * @param xblockElement The element that contains the xblock to be edited.
             * @param rootXBlockInfo An XBlockInfo model that describes the root xblock on the page.
             * @param options A standard options object.
             */
            edit: function(xblockElement, rootXBlockInfo, options) {
                this.xblockElement = xblockElement;
                this.containerInfo = rootXBlockInfo;
                this.xblockInfo = this.findXBlockInfo(xblockElement, rootXBlockInfo);
                this.options.modalType = this.xblockInfo.get('category');
                this.editOptions = options;
                this.show();
            },

            getContentHtml: function() {
                return this.template({
                    xblockInfo: this.xblockInfo
                });
            },

            getTitle: function() {
                var displayName = this.xblockInfo.get('display_name');
                if (!displayName) {
                    displayName = gettext('Component');
                }
                return interpolate(gettext("Editing visibility for: %(title)s"), { title: displayName }, true);
            },

            save: function(event) {
                var self = this,
                    editorView = this.editorView,
                    xblockInfo = this.xblockInfo,
                    data = editorView.getXModuleData();
                event.preventDefault();
                if (data) {
                    ViewUtils.runOperationShowingMessage(gettext('Saving'),
                        function() {
                            return xblockInfo.save(data);
                        }).done(function() {
                            self.onSave();
                        });
                }
            },

            onSave: function() {
                var refresh = this.editOptions.refresh;
                this.hide();
                if (refresh) {
                    refresh(this.xblockInfo);
                }
            },

            findXBlockInfo: function(xblockWrapperElement, defaultXBlockInfo) {
                var xblockInfo = defaultXBlockInfo,
                    xblockElement,
                    displayName;
                if (xblockWrapperElement.length > 0) {
                    xblockElement = xblockWrapperElement.find('.xblock');
                    displayName = xblockWrapperElement.find('.xblock-header .header-details .xblock-display-name').text().trim();
                    // If not found, try looking for the old unit page style rendering.
                    // Only used now by static pages.
                    if (!displayName) {
                        displayName = this.xblockElement.find('.component-header').text().trim();
                    }
                    xblockInfo = new XBlockInfo({
                        id: xblockWrapperElement.data('locator'),
                        courseKey: xblockWrapperElement.data('course-key'),
                        category: xblockElement.data('block-type'),
                        display_name: displayName
                    });
                }
                return xblockInfo;
            }
        });

        return VisibilityModal;
    });
