/**
 * XBlockContainerPage is used to display Studio's container page for an xblock which has children.
 * This page allows the user to understand and manipulate the xblock and its children.
 */
define(['jquery', 'underscore', 'backbone', 'gettext', 'js/views/pages/base_page',
    'common/js/components/utils/view_utils', 'js/views/container', 'js/views/xblock',
    'js/views/components/add_xblock', 'js/views/modals/edit_xblock', 'js/views/modals/move_xblock_modal',
    'js/models/xblock_info', 'js/views/xblock_string_field_editor', 'js/views/xblock_access_editor',
    'js/views/pages/container_subviews', 'js/views/unit_outline', 'js/views/utils/xblock_utils',
    'common/js/components/views/feedback_notification', 'common/js/components/views/feedback_prompt',
    'js/views/utils/tagging_drawer_utils', 'js/utils/module',
],
function($, _, Backbone, gettext, BasePage,
    ViewUtils, ContainerView, XBlockView,
    AddXBlockComponent, EditXBlockModal, MoveXBlockModal,
    XBlockInfo, XBlockStringFieldEditor, XBlockAccessEditor,
    ContainerSubviews, UnitOutlineView, XBlockUtils,
    NotificationView, PromptView, TaggingDrawerUtils, ModuleUtils) {
    'use strict';

    var XBlockContainerPage = BasePage.extend({
        // takes XBlockInfo as a model

        events: {
            'click .edit-button': 'editXBlock',
            'click .access-button': 'editVisibilitySettings',
            'click .duplicate-button': 'duplicateXBlock',
            'click .copy-button': 'copyXBlock',
            'click .move-button': 'showMoveXBlockModal',
            'click .delete-button': 'deleteXBlock',
            'click .show-actions-menu-button': 'showXBlockActionsMenu',
            'click .new-component-button': 'scrollToNewComponentButtons',
            'click .save-button': 'saveSelectedLibraryComponents',
            'click .paste-component-button': 'pasteComponent',
            'click .manage-tags-button': 'openManageTags',
            'change .header-library-checkbox': 'toggleLibraryComponent',
            'click .collapse-button': 'collapseXBlock',
        },

        options: {
            collapsedClass: 'is-collapsed',
            canEdit: true, // If not specified, assume user has permission to make changes
            clipboardData: { content: null },
        },

        view: 'container_preview',

        defaultViewClass: ContainerView,

        // Overridable by subclasses-- determines whether the XBlock component
        // addition menu is added on initialization. You may set this to false
        // if your subclass handles it.
        components_on_init: true,

        initialize: function(options) {
            BasePage.prototype.initialize.call(this, options);
            this.viewClass = options.viewClass || this.defaultViewClass;
            this.isLibraryPage = (this.model.attributes.category === 'library');
            this.isLibraryContentPage = (this.model.attributes.category === 'library_content');
            this.nameEditor = new XBlockStringFieldEditor({
                el: this.$('.wrapper-xblock-field'),
                model: this.model
            });
            this.nameEditor.render();
            if (!this.isLibraryPage) {
                this.accessEditor = new XBlockAccessEditor({
                    el: this.$('.wrapper-xblock-field')
                });
                this.accessEditor.render();
            }
            if (this.options.action === 'new') {
                this.nameEditor.$('.xblock-field-value-edit').click();
            }
            this.xblockView = this.getXBlockView();
            this.messageView = new ContainerSubviews.MessageView({
                el: this.$('.container-message'),
                model: this.model
            });
            this.messageView.render();
            this.clipboardBroadcastChannel = new BroadcastChannel("studio_clipboard_channel");
            // Display access message on units and split test components
            if (!this.isLibraryPage) {
                this.containerAccessView = new ContainerSubviews.ContainerAccess({
                    el: this.$('.container-access'),
                    model: this.model
                });
                this.containerAccessView.render();

                this.xblockPublisher = new ContainerSubviews.Publisher({
                    el: this.$('#publish-unit'),
                    model: this.model,
                    // When "Discard Changes" is clicked, the whole page must be re-rendered.
                    renderPage: this.render,
                    clipboardBroadcastChannel: this.clipboardBroadcastChannel,
                });
                this.xblockPublisher.render();

                this.publishHistory = new ContainerSubviews.PublishHistory({
                    el: this.$('#publish-history'),
                    model: this.model
                });
                this.publishHistory.render();

                this.viewLiveActions = new ContainerSubviews.ViewLiveButtonController({
                    el: this.$('.nav-actions'),
                    model: this.model
                });
                this.viewLiveActions.render();

                if (!this.model.get('is_tagging_feature_disabled')) {
                    this.tagListView = new ContainerSubviews.TagList({
                        el: this.$('.unit-tags'),
                        model: this.model
                    });
                    this.tagListView.setupMessageListener();
                    this.tagListView.render();
                }

                this.unitOutlineView = new UnitOutlineView({
                    el: this.$('.wrapper-unit-overview'),
                    model: this.model
                });
                this.unitOutlineView.render();

            }

            this.listenTo(Backbone, 'move:onXBlockMoved', this.onXBlockMoved);
        },

        getViewParameters: function() {
            return {
                el: this.$('.wrapper-xblock'),
                model: this.model,
                view: this.view
            };
        },

        getXBlockView: function() {
            return new this.viewClass(this.getViewParameters());
        },

        render: function(options) {
            var self = this,
                xblockView = this.xblockView,
                loadingElement = this.$('.ui-loading'),
                unitLocationTree = this.$('.unit-location'),
                unitTags = this.$('.unit-tags'),
                hiddenCss = 'is-hidden';

            loadingElement.removeClass(hiddenCss);

            // Hide both blocks until we know which one to show
            xblockView.$el.addClass(hiddenCss);

            // Render the xblock
            xblockView.render({
                done: function() {
                    // Show the xblock and hide the loading indicator
                    xblockView.$el.removeClass(hiddenCss);
                    loadingElement.addClass(hiddenCss);

                    // Notify the runtime that the page has been successfully shown
                    xblockView.notifyRuntime('page-shown', self);

                    if (self.components_on_init) {
                        // Render the add buttons. Paged containers should do this on their own.
                        self.renderAddXBlockComponents();
                    }

                    // Refresh the views now that the xblock is visible
                    self.onXBlockRefresh(xblockView);
                    unitLocationTree.removeClass(hiddenCss);
                    unitTags.removeClass(hiddenCss);

                    // Re-enable Backbone events for any updated DOM elements
                    self.delegateEvents();

                    // Show/hide the paste button
                    if (!self.isLibraryPage && !self.isLibraryContentPage) {
                        self.initializePasteButton();
                    }

                    var targetId = window.location.hash.slice(1);
                    if (targetId) {
                        var target = document.getElementById(targetId);
                        target.scrollIntoView({ behavior: 'smooth', inline: 'center' });
                    }

                },
                block_added: options && options.block_added
            });
        },

        findXBlockElement: function(target) {
            return $(target).closest('.studio-xblock-wrapper');
        },

        getURLRoot: function() {
            return this.xblockView.model.urlRoot;
        },

        onXBlockRefresh: function(xblockView, block_added, is_duplicate) {
            this.xblockView.refresh(xblockView, block_added, is_duplicate);
            // Update publish and last modified information from the server.
            this.model.fetch();
        },

        renderAddXBlockComponents: function() {
            var self = this;
            if (self.options.canEdit) {
                this.$('.add-xblock-component').each(function(index, element) {
                    var component = new AddXBlockComponent({
                        el: element,
                        createComponent: _.bind(self.createComponent, self),
                        collection: self.options.templates
                    });
                    component.render();
                });
            } else {
                this.$('.add-xblock-component').remove();
            }
        },

        initializePasteButton() {
            if (this.options.canEdit) {
                // We should have the user's clipboard status.
                const data = this.options.clipboardData;
                this.refreshPasteButton(data);
                // Refresh the status when something is copied on another tab:
                this.clipboardBroadcastChannel.onmessage = (event) => { this.refreshPasteButton(event.data); };
            } else {
                this.$(".paste-component").hide();
            }
        },

        /**
         * Given the latest information about the user's clipboard, hide or show the Paste button as appropriate.
         */
        refreshPasteButton(data) {
            // Do not perform any changes on paste button since they are not
            // rendered on Library or LibraryContent pages
            if (!this.isLibraryPage && !this.isLibraryContentPage) {
                // 'data' is the same data returned by the "get clipboard status" API endpoint
                // i.e. /api/content-staging/v1/clipboard/
                if (this.options.canEdit && data.content) {
                    if (["vertical", "sequential", "chapter", "course"].includes(data.content.block_type)) {
                        // This is not suitable for pasting into a unit.
                        this.$(".paste-component").hide();
                    } else if (data.content.status === "expired") {
                        // This has expired and can no longer be pasted.
                        this.$(".paste-component").hide();
                    } else {
                        // The thing in the clipboard can be pasted into this unit:
                        const detailsPopupEl = this.$(".clipboard-details-popup")[0];
                        detailsPopupEl.querySelector(".detail-block-name").innerText = data.content.display_name;
                        detailsPopupEl.querySelector(".detail-block-type").innerText = data.content.block_type_display;
                        detailsPopupEl.querySelector(".detail-course-name").innerText = data.source_context_title;
                        if (data.source_edit_url) {
                            detailsPopupEl.setAttribute("href", data.source_edit_url);
                            detailsPopupEl.classList.remove("no-edit-link");
                        } else {
                            detailsPopupEl.setAttribute("href", "#");
                            detailsPopupEl.classList.add("no-edit-link");
                        }
                        this.$(".paste-component").show();
                    }
                } else {
                    this.$(".paste-component").hide();
                }
            }
        },

        /** The user has clicked on the "Paste Component button" */
        pasteComponent(event) {
            event.preventDefault();
            // Get the ID of the container (usually a unit/vertical) that we're pasting into:
            const parentElement = this.findXBlockElement(event.target);
            const parentLocator = parentElement.data('locator');
            // Create a placeholder XBlock while we're pasting:
            const $placeholderEl = $(this.createPlaceholderElement());
            const addComponentsPanel = $(event.target).closest('.paste-component').prev();
            const listPanel = addComponentsPanel.prev();
            const scrollOffset = ViewUtils.getScrollOffset(addComponentsPanel);
            const placeholderElement = $placeholderEl.appendTo(listPanel);

            // Start showing a "Pasting" notification:
            ViewUtils.runOperationShowingMessage(gettext('Pasting'), () => {
                return $.postJSON(this.getURLRoot() + '/', {
                    parent_locator: parentLocator,
                    staged_content: "clipboard",
                }).then((data) => {
                    this.onNewXBlock(placeholderElement, scrollOffset, false, data);
                    return data;
                }).fail(() => {
                    // Remove the placeholder if the paste failed
                    placeholderElement.remove();
                });
            }).done((data) => {
                const {
                    conflicting_files: conflictingFiles,
                    error_files: errorFiles,
                    new_files: newFiles,
                } = data.static_file_notices;

                const notices = [];
                if (errorFiles.length) {
                    notices.push((next) => new PromptView.Error({
                        title: gettext("Some errors occurred"),
                        message: (
                            gettext("The following required files could not be added to the course:") +
                            " " + errorFiles.join(", ")
                        ),
                        actions: {primary: {text: gettext("OK"), click: (x) => { x.hide(); next(); }}},
                    }));
                }
                if (conflictingFiles.length) {
                    notices.push((next) => new PromptView.Warning({
                        title: gettext("You may need to update a file(s) manually"),
                        message: (
                            gettext(
                                "The following files already exist in this course but don't match the " +
                                "version used by the component you pasted:"
                            ) + " " + conflictingFiles.join(", ")
                        ),
                        actions: {primary: {text: gettext("OK"), click: (x) => { x.hide(); next(); }}},
                    }));
                }
                if (newFiles.length) {
                    notices.push(() => new NotificationView.Info({
                        title: gettext("New file(s) added to Files & Uploads."),
                        message: (
                            gettext("The following required files were imported to this course:") +
                            " "  + newFiles.join(", ")
                        ),
                        actions: {
                            primary: {
                                text: gettext('View files'),
                                click: function(notification) {
                                    const section = document.querySelector('[data-course-assets]');
                                    const assetsUrl = $(section).attr('data-course-assets');
                                    window.location.href = assetsUrl;
                                    return;
                                }
                            },
                            secondary: {
                                text: gettext('Dismiss'),
                                click: function(notification) {
                                    return notification.hide();
                                }
                            }
                        }
                    }));
                }
                if (notices.length) {
                    // Show the notices, one at a time:
                    const showNext = () => {
                        const view = notices.shift()(showNext);
                        view.show();
                    }
                    // Delay to avoid conflict with the "Pasting..." notification.
                    setTimeout(showNext, 1250);
                }
            });
        },

        editXBlock: function(event, options) {
            event.preventDefault();

            if (!options || options.view !== 'visibility_view') {
                const primaryHeader = $(event.target).closest('.xblock-header-primary, .nav-actions');

                var useNewTextEditor = primaryHeader.attr('use-new-editor-text'),
                    useNewVideoEditor = primaryHeader.attr('use-new-editor-video'),
                    useNewProblemEditor = primaryHeader.attr('use-new-editor-problem'),
                    blockType = primaryHeader.attr('data-block-type');

                if((useNewTextEditor === 'True' && blockType === 'html')
                        || (useNewVideoEditor === 'True' && blockType === 'video')
                        || (useNewProblemEditor === 'True' && blockType === 'problem')
                ) {
                    var destinationUrl = primaryHeader.attr('authoring_MFE_base_url') + '/' + blockType + '/' + encodeURI(primaryHeader.attr('data-usage-id'));
                    window.location.href = destinationUrl;
                    return;
                }
            }

            var xblockElement = this.findXBlockElement(event.target),
                self = this,
                modal = new EditXBlockModal(options);

            modal.edit(xblockElement, this.model, {
                readOnlyView: !this.options.canEdit,
                refresh: function() {
                    self.refreshXBlock(xblockElement, false);
                }
            });
        },

        /**
         * If the new "Actions" menu is enabled, most XBlock actions like
         * Duplicate, Move, Delete, Manage Access, etc. are moved into this
         * menu. For this event, we just toggle displaying the menu.
         * @param {*} event
         */
        showXBlockActionsMenu: function(event) {
            const showActionsButton = event.currentTarget;
            const subMenu = showActionsButton.parentElement.querySelector('.wrapper-nav-sub');

            // Close all open dropdowns
            const elements = document.querySelectorAll("li.action-item.action-actions-menu.nav-item");
            elements.forEach(element => {
                if (element !== showActionsButton.parentElement) {
                    element.querySelector('.wrapper-nav-sub').classList.remove('is-shown');
                }
            });

            // Code in 'base.js' normally handles toggling these dropdowns but since this one is
            // not present yet during the domReady event, we have to handle displaying it ourselves.
            subMenu.classList.toggle('is-shown');
            // if propagation is not stopped, the event will bubble up to the
            // body element, which will close the dropdown.
            event.stopPropagation();
        },

        editVisibilitySettings: function(event) {
            this.editXBlock(event, {
                view: 'visibility_view',
                // Translators: "title" is the name of the current component or unit being edited.
                titleFormat: gettext('Editing access for: {title}'),
                viewSpecificClasses: '',
                modalSize: 'med'
            });
        },

        duplicateXBlock: function(event) {
            event.preventDefault();
            this.duplicateComponent(this.findXBlockElement(event.target));
        },

        openManageTags: function(event) {
            const taxonomyTagsWidgetUrl = this.model.get('taxonomy_tags_widget_url');
            const contentId = this.findXBlockElement(event.target).data('locator');

            TaggingDrawerUtils.openDrawer(taxonomyTagsWidgetUrl, contentId);
        },

        showMoveXBlockModal: function(event) {
            var xblockElement = this.findXBlockElement(event.target),
                parentXBlockElement = xblockElement.parents('.studio-xblock-wrapper'),
                modal = new MoveXBlockModal({
                    sourceXBlockInfo: XBlockUtils.findXBlockInfo(xblockElement, this.model),
                    sourceParentXBlockInfo: XBlockUtils.findXBlockInfo(parentXBlockElement, this.model),
                    XBlockURLRoot: this.getURLRoot(),
                    outlineURL: this.options.outlineURL
                });

            event.preventDefault();
            modal.show();
        },

        deleteXBlock: function(event) {
            event.preventDefault();
            this.deleteComponent(this.findXBlockElement(event.target));
        },

        createPlaceholderElement: function() {
            return $('<div/>', {class: 'studio-xblock-wrapper'});
        },

        createComponent: function(template, target) {
            // A placeholder element is created in the correct location for the new xblock
            // and then onNewXBlock will replace it with a rendering of the xblock. Note that
            // for xblocks that can't be replaced inline, the entire parent will be refreshed.
            var parentElement = this.findXBlockElement(target),
                parentLocator = parentElement.data('locator'),
                buttonPanel = target.closest('.add-xblock-component'),
                listPanel = buttonPanel.prev(),
                scrollOffset = ViewUtils.getScrollOffset(buttonPanel),
                $placeholderEl = $(this.createPlaceholderElement()),
                requestData = _.extend(template, {
                    parent_locator: parentLocator
                }),
                placeholderElement;
            placeholderElement = $placeholderEl.appendTo(listPanel);
            return $.postJSON(this.getURLRoot() + '/', requestData,
                _.bind(this.onNewXBlock, this, placeholderElement, scrollOffset, false))
                .fail(function() {
                    // Remove the placeholder if the update failed
                    placeholderElement.remove();
                });
        },

        copyXBlock: function(event) {
            event.preventDefault();
            const clipboardEndpoint = "/api/content-staging/v1/clipboard/";
            const element = this.findXBlockElement(event.target);
            const usageKeyToCopy = element.data('locator');
            // Start showing a "Copying" notification:
            ViewUtils.runOperationShowingMessage(gettext('Copying'), () => {
                return $.postJSON(
                    clipboardEndpoint,
                    { usage_key: usageKeyToCopy },
                ).then((data) => {
                    const status = data.content?.status;
                    if (status === "ready") {
                        // The XBlock has been copied and is ready to use.
                        this.refreshPasteButton(data); // Update our UI
                        this.clipboardBroadcastChannel.postMessage(data); // And notify any other open tabs
                        return data;
                    } else if (status === "loading") {
                        // The clipboard is being loaded asynchonously.
                        // Poll the endpoint until the copying process is complete:
                        const deferred = $.Deferred();
                        const checkStatus = () => {
                            $.getJSON(clipboardEndpoint, (pollData) => {
                                const newStatus = pollData.content?.status;
                                if (newStatus === "ready") {
                                    this.refreshPasteButton(data);
                                    this.clipboardBroadcastChannel.postMessage(pollData);
                                    deferred.resolve(pollData);
                                } else if (newStatus === "loading") {
                                    setTimeout(checkStatus, 1_000);
                                } else {
                                    deferred.reject();
                                    throw new Error(`Unexpected clipboard status "${newStatus}" in successful API response.`);
                                }
                            })
                        }
                        setTimeout(checkStatus, 1_000);
                        return deferred;
                    } else {
                        throw new Error(`Unexpected clipboard status "${status}" in successful API response.`);
                    }
                });
            });
        },

        duplicateComponent: function(xblockElement) {
            // A placeholder element is created in the correct location for the duplicate xblock
            // and then onNewXBlock will replace it with a rendering of the xblock. Note that
            // for xblocks that can't be replaced inline, the entire parent will be refreshed.
            var self = this,
                parentElement = self.findXBlockElement(xblockElement.parent()),
                scrollOffset = ViewUtils.getScrollOffset(xblockElement),
                $placeholderEl = $(self.createPlaceholderElement()),
                placeholderElement;

            placeholderElement = $placeholderEl.insertAfter(xblockElement);
            XBlockUtils.duplicateXBlock(xblockElement, parentElement)
                .done(function(data) {
                    self.onNewXBlock(placeholderElement, scrollOffset, true, data);
                })
                .fail(function() {
                    // Remove the placeholder if the update failed
                    placeholderElement.remove();
                });
        },

        duplicateXBlock: function(event) {
            event.preventDefault();
            this.duplicateComponent(this.findXBlockElement(event.target));
        },

        showMoveXBlockModal: function(event) {
            var xblockElement = this.findXBlockElement(event.target),
                parentXBlockElement = xblockElement.parents('.studio-xblock-wrapper'),
                modal = new MoveXBlockModal({
                sourceXBlockInfo: XBlockUtils.findXBlockInfo(xblockElement, this.model),
                sourceParentXBlockInfo: XBlockUtils.findXBlockInfo(parentXBlockElement, this.model),
                XBlockURLRoot: this.getURLRoot(),
                outlineURL: this.options.outlineURL
            });

            event.preventDefault();
            modal.show();
        },

        deleteXBlock: function(event) {
            event.preventDefault();
            this.deleteComponent(this.findXBlockElement(event.target));
        },

        createPlaceholderElement: function() {
            return $('<div/>', {class: 'studio-xblock-wrapper'});
        },

        createComponent: function(template, target) {
            // A placeholder element is created in the correct location for the new xblock
            // and then onNewXBlock will replace it with a rendering of the xblock. Note that
            // for xblocks that can't be replaced inline, the entire parent will be refreshed.
            var parentElement = this.findXBlockElement(target),
                parentLocator = parentElement.data('locator'),
                buttonPanel = target.closest('.add-xblock-component'),
                listPanel = buttonPanel.prev(),
                scrollOffset = ViewUtils.getScrollOffset(buttonPanel),
                $placeholderEl = $(this.createPlaceholderElement()),
                requestData = _.extend(template, {
                    parent_locator: parentLocator
                }),
                placeholderElement;
            placeholderElement = $placeholderEl.appendTo(listPanel);
            return $.postJSON(this.getURLRoot() + '/', requestData,
                _.bind(this.onNewXBlock, this, placeholderElement, scrollOffset, false))
                .fail(function() {
                    // Remove the placeholder if the update failed
                    placeholderElement.remove();
            });
        },

        duplicateComponent: function(xblockElement) {
            // A placeholder element is created in the correct location for the duplicate xblock
            // and then onNewXBlock will replace it with a rendering of the xblock. Note that
            // for xblocks that can't be replaced inline, the entire parent will be refreshed.
            var self = this,
                parentElement = self.findXBlockElement(xblockElement.parent()),
                scrollOffset = ViewUtils.getScrollOffset(xblockElement),
                $placeholderEl = $(self.createPlaceholderElement()),
                placeholderElement;

            placeholderElement = $placeholderEl.insertAfter(xblockElement);
            XBlockUtils.duplicateXBlock(xblockElement, parentElement)
                .done(function(data) {
                    self.onNewXBlock(placeholderElement, scrollOffset, true, data);
                })
                .fail(function() {
                    // Remove the placeholder if the update failed
                    placeholderElement.remove();
                });
        },

        deleteComponent: function(xblockElement) {
            var self = this,
                xblockInfo = new XBlockInfo({
                    id: xblockElement.data('locator')
                });
            XBlockUtils.deleteXBlock(xblockInfo).done(function() {
                self.onDelete(xblockElement);
            });
        },

        getSelectedLibraryComponents: function() {
            var self = this;
            var locator = this.$el.find('.studio-xblock-wrapper').data('locator');
            console.log(ModuleUtils);
            $.getJSON(
                ModuleUtils.getUpdateUrl(locator) + '/handler/get_block_ids',
                function(data) {
                    self.selectedLibraryComponents = Array.from(data.source_block_ids);
                    self.storedSelectedLibraryComponents = Array.from(data.source_block_ids);
                }
            );
        },

        saveSelectedLibraryComponents: function(e) {
            var self = this;
            var locator = this.$el.find('.studio-xblock-wrapper').data('locator');
            e.preventDefault();
            $.postJSON(
                ModuleUtils.getUpdateUrl(locator) + '/handler/submit_studio_edits',
                {values: {source_block_ids: self.storedSelectedLibraryComponents}},
                function() {
                    self.selectedLibraryComponents = Array.from(self.storedSelectedLibraryComponents);
                    self.toggleSaveButton();
                }
            );
        },

        toggleLibraryComponent: function(event) {
            var componentId = $(event.target).closest('.studio-xblock-wrapper').data('locator');
            var storeIndex = this.storedSelectedLibraryComponents.indexOf(componentId);
            if (storeIndex > -1) {
                this.storedSelectedLibraryComponents.splice(storeIndex, 1);
                this.toggleSaveButton();
            } else {
                this.storedSelectedLibraryComponents.push(componentId);
                this.toggleSaveButton();
            }
        },

        toggleSaveButton: function() {
            var $saveButton = $('.nav-actions .save-button');
            if (JSON.stringify(this.selectedLibraryComponents.sort()) === JSON.stringify(this.storedSelectedLibraryComponents.sort())) {
                $saveButton.addClass('is-hidden');
                window.removeEventListener('beforeunload', this.onBeforePageUnloadCallback);
            } else {
                $saveButton.removeClass('is-hidden');
                window.addEventListener('beforeunload', this.onBeforePageUnloadCallback);
            }
        },

        onBeforePageUnloadCallback: function (event) {
            event.preventDefault();
            event.returnValue = '';
        },

        onDelete: function(xblockElement) {
            // get the parent so we can remove this component from its parent.
            var xblockView = this.xblockView,
                parent = this.findXBlockElement(xblockElement.parent());
            xblockElement.remove();

            // Inform the runtime that the child has been deleted in case
            // other views are listening to deletion events.
            xblockView.acknowledgeXBlockDeletion(parent.data('locator'));

            // Update publish and last modified information from the server.
            this.model.fetch();
        },

        /*
         * After move operation is complete, updates the xblock information from server .
         */
        onXBlockMoved: function() {
            this.model.fetch();
        },

        onNewXBlock: function(xblockElement, scrollOffset, is_duplicate, data) {
            var useNewTextEditor = this.$('.xblock-header-primary').attr('use-new-editor-text'),
                useNewVideoEditor = this.$('.xblock-header-primary').attr('use-new-editor-video'),
                useVideoGalleryFlow = this.$('.xblock-header-primary').attr("use-video-gallery-flow"),
                useNewProblemEditor = this.$('.xblock-header-primary').attr('use-new-editor-problem');

            // find the block type in the locator if availible
            if(data.hasOwnProperty('locator')) {
                var matchBlockTypeFromLocator = /\@(.*?)\+/;
                var blockType = data.locator.match(matchBlockTypeFromLocator);
            }
            if((useNewTextEditor === 'True' && blockType.includes('html'))
                    || (useNewVideoEditor === 'True' && blockType.includes('video'))
                    || (useNewProblemEditor === 'True' && blockType.includes('problem'))
            ){
                var destinationUrl;
                if (useVideoGalleryFlow === "True" && blockType.includes("video")) {
                    destinationUrl = this.$('.xblock-header-primary').attr("authoring_MFE_base_url") + '/course-videos/' + encodeURI(data.locator);
                }
                else {
                    destinationUrl = this.$('.xblock-header-primary').attr("authoring_MFE_base_url") + '/' + blockType[1] + '/' + encodeURI(data.locator);
                }
                window.location.href = destinationUrl;
                return;
            }
            ViewUtils.setScrollOffset(xblockElement, scrollOffset);
            xblockElement.data('locator', data.locator);
            return this.refreshXBlock(xblockElement, true, is_duplicate);
        },

        /**
         * Refreshes the specified xblock's display. If the xblock is an inline child of a
         * reorderable container then the element will be refreshed inline. If not, then the
         * parent container will be refreshed instead.
         * @param element An element representing the xblock to be refreshed.
         * @param block_added Flag to indicate that new block has been just added.
         */
        refreshXBlock: function(element, block_added, is_duplicate) {
            var xblockElement = this.findXBlockElement(element),
                parentElement = xblockElement.parent(),
                rootLocator = this.xblockView.model.id;
            if (xblockElement.length === 0 || xblockElement.data('locator') === rootLocator) {
                this.render({refresh: true, block_added: block_added});
            } else if (parentElement.hasClass('reorderable-container')) {
                this.refreshChildXBlock(xblockElement, block_added, is_duplicate);
            } else {
                this.refreshXBlock(this.findXBlockElement(parentElement));
            }
        },

        /**
         * Refresh an xblock element inline on the page, using the specified xblockInfo.
         * Note that the element is removed and replaced with the newly rendered xblock.
         * @param xblockElement The xblock element to be refreshed.
         * @param block_added Specifies if a block has been added, rather than just needs
         * refreshing.
         * @returns {jQuery promise} A promise representing the complete operation.
         */
        refreshChildXBlock: function(xblockElement, block_added, is_duplicate) {
            var self = this,
                xblockInfo,
                TemporaryXBlockView,
                temporaryView;
            xblockInfo = new XBlockInfo({
                id: xblockElement.data('locator')
            });
            // There is only one Backbone view created on the container page, which is
            // for the container xblock itself. Any child xblocks rendered inside the
            // container do not get a Backbone view. Thus, create a temporary view
            // to render the content, and then replace the original element with the result.
            TemporaryXBlockView = XBlockView.extend({
                updateHtml: function(element, html) {
                    // Replace the element with the new HTML content, rather than adding
                    // it as child elements.
                    this.$el = $(html).replaceAll(element); // xss-lint: disable=javascript-jquery-insertion
                }
            });
            temporaryView = new TemporaryXBlockView({
                model: xblockInfo,
                view: self.xblockView.new_child_view,
                el: xblockElement
            });
            return temporaryView.render({
                success: function() {
                    self.onXBlockRefresh(temporaryView, block_added, is_duplicate);
                    temporaryView.unbind(); // Remove the temporary view
                },
                initRuntimeData: this
            });
        },

        scrollToNewComponentButtons: function(event) {
            event.preventDefault();
            $.scrollTo(this.$('.add-xblock-component'), {duration: 250});
        }
    });

    return XBlockContainerPage;
}); // end define();
