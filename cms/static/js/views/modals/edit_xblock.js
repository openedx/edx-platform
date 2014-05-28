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
                "click .action-modes a": "changeMode"
            },

            options: $.extend({}, BaseModal.prototype.options, {
                modalName: 'edit-xblock',
                addSaveButton: true
            }),

            initialize: function() {
                BaseModal.prototype.initialize.call(this);
                this.events = _.extend({}, BaseModal.prototype.events, this.events);
                this.template = this.loadTemplate('edit-xblock-modal');
                this.editorModeButtonTemplate = this.loadTemplate('editor-mode-button');
            },

            /**
             * Show an edit modal for the specified xblock
             * @param xblockElement The element that contains the xblock to be edited.
             * @param rootXBlockInfo An XBlockInfo model that describes the root xblock on the page.
             * @param options A standard options object.
             */
            edit: function(xblockElement, rootXBlockInfo, options) {
                this.xblockElement = xblockElement;
                this.xblockInfo = this.findXBlockInfo(xblockElement, rootXBlockInfo);
                this.options.modalType = this.xblockInfo.get('category');
                this.editOptions = options;
                this.render();
                this.show();

                // Hide the action bar until we know which buttons we want
                this.getActionBar().hide();

                // Display the xblock after the modal is shown as there are some xblocks
                // that depend upon being visible when they initialize, e.g. the problem xmodule.
                this.displayXBlock();
            },

            getContentHtml: function() {
                return this.template({
                    xblockInfo: this.xblockInfo
                });
            },

            displayXBlock: function() {
                this.editorView = new XBlockEditorView({
                    el: this.$('.xblock-editor'),
                    model: this.xblockInfo
                });
                this.editorView.render({
                    success: _.bind(this.onDisplayXBlock, this)
                });
            },

            onDisplayXBlock: function() {
                var editorView = this.editorView,
                    title = this.getTitle(),
                    xblock = editorView.xblock,
                    runtime = xblock.runtime;

                // Notify the runtime that the modal has been shown
                if (runtime) {
                    this.runtime = runtime;
                    runtime.notify("edit-modal-shown", this);
                }

                // Update the modal's header
                if (editorView.hasCustomTabs()) {
                    // Hide the modal's header as the custom editor provides its own
                    this.$('.modal-header').hide();

                    // Update the custom editor's title
                    editorView.$('.component-name').text(title);
                } else {
                    this.$('.modal-window-title').text(title);
                    if (editorView.getDataEditor() && editorView.getMetadataEditor()) {
                        this.addDefaultModes();
                        this.selectMode(editorView.mode);
                    }
                }

                // If the xblock is not using custom buttons then choose which buttons to show
                if (!editorView.hasCustomButtons()) {
                    // If the xblock does not support save then disable the save button
                    if (!xblock.save) {
                        this.disableSave();
                    }
                    this.getActionBar().show();
                }

                // Resize the modal to fit the window
                this.resize();
            },

            disableSave: function() {
                var saveButton = this.getActionButton('save'),
                    cancelButton = this.getActionButton('cancel');
                saveButton.hide();
                cancelButton.text(gettext('OK'));
                cancelButton.addClass('action-primary');
            },

            getTitle: function() {
                var displayName = this.xblockElement.find('.xblock-header .header-details').text().trim();
                // If not found, try the old unit page style rendering
                if (!displayName) {
                    displayName = this.xblockElement.find('.component-header').text().trim();
                    if (!displayName) {
                        displayName = gettext('Component');
                    }
                }
                return interpolate(gettext("Editing: %(title)s"), { title: displayName }, true);
            },

            addDefaultModes: function() {
                var defaultModes, i, mode;
                defaultModes = this.editorView.getDefaultModes();
                for (i = 0; i < defaultModes.length; i++) {
                    mode = defaultModes[i];
                    this.addModeButton(mode.id, mode.name);
                }
            },

            changeMode: function(event) {
                this.removeCheatsheetVisibility();
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

            save: function(event) {
                event.preventDefault();
                this.editorView.save({
                    success: _.bind(this.onSave, this)
                });
            },

            onSave: function() {
                var refresh = this.editOptions.refresh;
                this.hide();
                if (refresh) {
                    refresh(this.xblockInfo);
                }
            },

            hide: function() {
                BaseModal.prototype.hide.call(this);

                // Notify the runtime that the modal has been hidden
                if (this.runtime) {
                    this.runtime.notify('edit-modal-hidden');
                }

                // Completely clear the contents of the modal
                this.undelegateEvents();
                this.$el.html("");
            },

            findXBlockInfo: function(xblockWrapperElement, defaultXBlockInfo) {
                var xblockInfo = defaultXBlockInfo,
                    xblockElement;
                if (xblockWrapperElement.length > 0) {
                    xblockElement = xblockWrapperElement.find('.xblock');
                    xblockInfo = new XBlockInfo({
                        id: xblockWrapperElement.data('locator'),
                        courseKey: xblockWrapperElement.data('course-key'),
                        category: xblockElement.data('block-type')
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
            },

            removeCheatsheetVisibility: function() {
                var cheatsheet = $('article.simple-editor-open-ended-cheatsheet');
                if (cheatsheet.length === 0) {
                    cheatsheet = $('article.simple-editor-cheatsheet');
                }
                if (cheatsheet.hasClass('shown')) {
                    cheatsheet.removeClass('shown');
                    $('.modal-content').removeClass('cheatsheet-is-shown');
                }
            }
        });

        return EditXBlockModal;
    });
