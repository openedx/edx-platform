/**
 * The EditXBlockModal is a Backbone view that shows an xblock editor in a modal window.
 * It is invoked using the edit method which is passed an existing rendered xblock,
 * and upon save an optional refresh function can be invoked to update the display.
 */
define(["jquery", "underscore", "gettext", "js/views/modals/base_modal",
    "js/models/xblock_info", "js/views/xblock_editor"],
    function($, _, gettext, BaseModal, XBlockInfo, XBlockEditorView) {
        var EditXBlockModal = BaseModal.extend({
            events : {
                "click .action-save": "save",
                "click .action-cancel": "cancel",
                "click .action-modes a": "changeMode"
            },

            initialize: function() {
                this.template = _.template($("#edit-xblock-modal-tpl").text());
                this.editorModeButtonTemplate = _.template($("#editor-mode-button-tpl").text());
            },

            /**
             * Show an edit modal for the specified xblock
             * @param xblockElement The
             * @param rootXBlockInfo
             * @param options
             */
            edit: function(xblockElement, rootXBlockInfo, options) {
                this.xblockElement = xblockElement;
                this.xblockInfo = this.findXBlockInfo(xblockElement, rootXBlockInfo);
                this.editOptions = options;
                this.render();
                this.show();
                // Display the xblock after the modal is shown as there are some xblocks
                // that depend upon being visible when they initialize, e.g. the problem xmodule.
                this.displayXBlock();
            },

            render: function() {
                var xblockInfo = this.xblockInfo;
                this.$el.html(this.template({
                    xblockInfo: xblockInfo
                }));
            },

            displayXBlock: function() {
                var xblockInfo = this.xblockInfo,
                    editorView = new XBlockEditorView({
                        el: this.$('.xblock-editor'),
                        model: xblockInfo
                    });
                this.editorView = editorView;
                editorView.render({
                    success: _.bind(this.onDisplayXBlock, this)
                });
            },

            onDisplayXBlock: function() {
                var editorView = this.editorView,
                    displayName,
                    title;
                displayName = editorView.getDisplayName();
                title = interpolate(gettext("Editing: %(title)s"), { title: displayName }, true);
                if (editorView.hasCustomTabs()) {
                    // Hide the modal's header as the custom editor provides its own
                    this.$('.modal-header').hide();

                    // Update the custom editor's title
                    editorView.$('.component-name').text(title);
                } else {
                    this.$('.modal-window-title').text(title);
                    if (editorView.getMetadataEditor()) {
                        this.addModeButton('editor', gettext("Editor"));
                        this.addModeButton('settings', gettext("Settings"));
                        this.selectMode(editorView.mode);
                    }
                }
            },

            changeMode: function(event) {
                var parent = $(event.target.parentElement),
                    mode = parent.data('mode');
                event.preventDefault();
                this.selectMode(mode);
            },

            selectMode: function(mode) {
                var editorView = this.editorView,
                    buttonSelector;
                editorView.selectMode(mode);
                this.$('.editor-modes a').removeClass('is-set');
                if (mode) {
                    buttonSelector = '.' + mode + '-button';
                    this.$(buttonSelector).addClass('is-set');
                }
            },

            cancel: function(event) {
                event.preventDefault();
                this.hide();
            },

            save: function(event) {
                var self = this,
                    xblockInfo = this.xblockInfo,
                    refresh = self.editOptions.refresh;
                event.preventDefault();
                this.editorView.save({
                    success: function() {
                        self.hide();
                        self.$el.html("");
                        if (refresh) {
                            refresh(xblockInfo);
                        }
                    }
                });
            },

            hide: function() {
                BaseModal.prototype.hide.call(this);

                // Completely clear the contents of the modal
                this.undelegateEvents();
                this.$el.html("");
            },

            findXBlockInfo: function(xblockElement, defaultXBlockInfo) {
                var xblockInfo = defaultXBlockInfo,
                    locator,
                    displayName,
                    category;
                if (xblockElement.length > 0) {
                    locator = xblockElement.data('locator');
                    displayName = xblockElement.data('display-name');
                    category = xblockElement.data('category');
                    if (!displayName) {
                        displayName = category;
                        if (!category) {
                            displayName = gettext('Empty');
                        }
                    }
                    xblockInfo = new XBlockInfo({
                        id: locator,
                        display_name: displayName,
                        category: category
                    });
                }
                return xblockInfo;
            },

            addModeButton: function(mode, displayName) {
                var buttonPanel = this.$('.editor-modes');
                buttonPanel.append(this.editorModeButtonTemplate({
                    mode: mode,
                    displayName: displayName
                }));
            }
        });

        return EditXBlockModal;
    });
