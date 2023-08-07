/**
 * The CourseOutlineView is used to render the contents of the course for the Course Outline page.
 * It is a recursive set of views, where each XBlock has its own instance, and each of the children
 * are shown as child CourseOutlineViews.
 *
 * This class extends XBlockOutlineView to add unique capabilities needed by the course outline:
 *  - sections are initially expanded but subsections and other children are shown as collapsed
 *  - changes cause a refresh of the entire section rather than just the view for the changed xblock
 *  - adding units will automatically redirect to the unit page rather than showing them inline
 */
define(['jquery', 'underscore', 'js/views/xblock_outline', 'common/js/components/utils/view_utils', 'js/views/utils/xblock_utils',
    'js/models/xblock_outline_info', 'js/views/modals/course_outline_modals', 'js/utils/drag_and_drop'],
function(
    $, _, XBlockOutlineView, ViewUtils, XBlockViewUtils,
    XBlockOutlineInfo, CourseOutlineModalsFactory, ContentDragger
) {
    var CourseOutlineView = XBlockOutlineView.extend({
        // takes XBlockOutlineInfo as a model

        templateName: 'course-outline',

        initialize: function() {
            XBlockOutlineView.prototype.initialize.call(this);
            this.clipboardBroadcastChannel = new BroadcastChannel("studio_clipboard_channel");
        },

        render: function() {
            var renderResult = XBlockOutlineView.prototype.render.call(this);
            this.makeContentDraggable(this.el);
            // Show/hide the paste button
            this.initializePasteButton(this.el);
            return renderResult;
        },

        shouldExpandChildren: function() {
            return this.expandedLocators.contains(this.model.get('id'));
        },

        shouldRenderChildren: function() {
            // Render all nodes up to verticals but not below
            return !this.model.isVertical();
        },

        getChildViewClass: function() {
            return CourseOutlineView;
        },

        /**
             * Refresh the containing section (if there is one) or else refresh the entire course.
             * Note that the refresh will preserve the expanded state of this view and all of its
             * children.
             * @param viewState The desired initial state of the view, or null if none.
             * @returns {jQuery promise} A promise representing the refresh operation.
             */
        refresh: function(viewState) {
            var getViewToRefresh, view, expandedLocators;

            // eslint-disable-next-line no-shadow
            getViewToRefresh = function(view) {
                if (view.model.isChapter() || !view.parentView) {
                    return view;
                }
                return getViewToRefresh(view.parentView);
            };

            view = getViewToRefresh(this);
            viewState = viewState || {};
            view.initialState = viewState;
            return view.model.fetch({});
        },

        /**
             * Updates the collapse/expand state for this outline element, and then calls refresh.
             * @param isCollapsed true if the element should be collapsed, else false
             */
        refreshWithCollapsedState: function(isCollapsed) {
            var locator = this.model.get('id');
            if (isCollapsed) {
                this.expandedLocators.remove(locator);
            } else {
                this.expandedLocators.add(locator);
            }
            this.refresh();
        },

        onChildAdded: function(locator, category, event) {
            if (category === 'vertical') {
                // For units, redirect to the new unit's page in inline edit mode
                this.onUnitAdded(locator);
            } else if (category === 'chapter' && this.model.hasChildren()) {
                this.onSectionAdded(locator);
            } else {
                // For all other block types, refresh the view and do the following:
                //  - show the new block expanded
                //  - ensure it is scrolled into view
                //  - make its name editable
                this.refresh(this.createNewItemViewState(locator, ViewUtils.getScrollOffset($(event.target))));
            }
        },

        /**
             * Perform specific actions for duplicated xblock.
             * @param {String}  locator  The locator of the new duplicated xblock.
             * @param {String}  xblockType The front-end terminology of the xblock category.
             * @param {jquery Element}  xblockElement  The xblock element to be duplicated.
             */
        onChildDuplicated: function(locator, xblockType, xblockElement) {
            var scrollOffset = ViewUtils.getScrollOffset(xblockElement);
            if (xblockType === 'section') {
                this.onSectionAdded(locator, xblockElement, scrollOffset);
            } else {
                // For all other block types, refresh the view and do the following:
                //  - show the new block expanded
                //  - ensure it is scrolled into view
                //  - make its name editable
                this.refresh(this.createNewItemViewState(locator, scrollOffset));
            }
        },

        onSectionAdded: function(locator, xblockElement, scrollOffset) {
            var self = this,
                initialState = self.createNewItemViewState(locator, scrollOffset),
                sectionInfo, sectionView;
                // For new chapters in a non-empty view, add a new child view and render it
                // to avoid the expense of refreshing the entire page.
            if (this.model.hasChildren()) {
                sectionInfo = new XBlockOutlineInfo({
                    id: locator,
                    category: 'chapter'
                });
                // Fetch the full xblock info for the section and then create a view for it
                sectionInfo.fetch().done(function() {
                    sectionView = self.createChildView(sectionInfo, self.model, {parentView: self});
                    sectionView.initialState = initialState;
                    sectionView.expandedLocators = self.expandedLocators;
                    sectionView.render();
                    self.addChildView(sectionView, xblockElement);
                    sectionView.setViewState(initialState);
                });
            } else {
                this.refresh(initialState);
            }
        },

        onChildDeleted: function(childView) {
            var xblockInfo = this.model,
                children = xblockInfo.get('child_info') && xblockInfo.get('child_info').children;
                // If deleting a section that isn't the final one, just remove it for efficiency
                // as it cannot visually effect the other sections.
            if (childView.model.isChapter() && children && children.length > 1) {
                childView.$el.remove();
                children.splice(children.indexOf(childView.model), 1);
            } else {
                this.refresh();
            }
        },

        createNewItemViewState: function(locator, scrollOffset) {
            this.expandedLocators.add(locator);
            return {
                locator_to_show: locator,
                edit_display_name: true,
                scroll_offset: scrollOffset || 0
            };
        },

        editXBlock: function() {
            var modal;
            var enableProctoredExams = false;
            var enableTimedExams = false;
            var unitLevelDiscussions = false;
            if (this.model.get('category') === 'sequential') {
                if (this.parentView.parentView.model.has('enable_proctored_exams')) {
                    enableProctoredExams = this.parentView.parentView.model.get('enable_proctored_exams');
                }
                if (this.parentView.parentView.model.has('enable_timed_exams')) {
                    enableTimedExams = this.parentView.parentView.model.get('enable_timed_exams');
                }
            }
            if (this.model.get('category') === 'vertical') {
                unitLevelDiscussions = this.parentView.parentView.parentView.model.get('unit_level_discussions');
            }
            modal = CourseOutlineModalsFactory.getModal('edit', this.model, {
                onSave: this.refresh.bind(this),
                parentInfo: this.parentInfo,
                enable_proctored_exams: enableProctoredExams,
                enable_timed_exams: enableTimedExams,
                unit_level_discussions: unitLevelDiscussions,
                xblockType: XBlockViewUtils.getXBlockType(
                    this.model.get('category'), this.parentView.model, true
                )
            });

            if (modal) {
                modal.show();
            }
        },

        publishXBlock: function() {
            var modal = CourseOutlineModalsFactory.getModal('publish', this.model, {
                onSave: this.refresh.bind(this),
                xblockType: XBlockViewUtils.getXBlockType(
                    this.model.get('category'), this.parentView.model, true
                )
            });

            if (modal) {
                modal.show();
            }
        },

        /** Copy a Unit to the clipboard */
        copyXBlock() {
            const clipboardEndpoint = "/api/content-staging/v1/clipboard/";
            // Start showing a "Copying" notification:
            ViewUtils.runOperationShowingMessage(gettext('Copying'), () => {
                return $.postJSON(
                    clipboardEndpoint,
                    { usage_key: this.model.get('id') },
                ).then((data) => {
                    const status = data.content?.status;
                    if (status === "ready") {
                        // The Unit has been copied and is ready to use.
                        this.refreshPasteButton(data); // Update our UI
                        this.clipboardBroadcastChannel.postMessage(data); // And notify any other open tabs
                        return data;
                    } else if (status === "loading") {
                        // The clipboard is being loaded asynchronously.
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

        initializePasteButton(element) {
            if ($(element).hasClass('outline-subsection')) {
                if (this.options.canEdit) {
                    // We should have the user's clipboard status.
                    const data = this.options.clipboardData;
                    this.refreshPasteButton(data);
                    // Refresh the status when something is copied on another tab:
                    this.clipboardBroadcastChannel.onmessage = (event) => { this.refreshPasteButton(event.data); };
                } else {
                    this.$(".paste-component").hide();
                }
            }
        },

        /**
         * Given the latest information about the user's clipboard, hide or show the Paste button as appropriate.
         */
        refreshPasteButton(data) {
            // 'data' is the same data returned by the "get clipboard status" API endpoint
            // i.e. /api/content-staging/v1/clipboard/
            if (this.options.canEdit && data.content) {
                if (data.content.status === "expired") {
                    // This has expired and can no longer be pasted.
                    this.$(".paste-component").hide();
                } else if (data.content.block_type_display === 'Unit') {
                    // This is suitable for pasting into a unit.
                    const detailsPopupEl = this.$(".clipboard-details-popup")[0];
                    // Only Units should have the paste button initialized
                    if (detailsPopupEl !== undefined) {
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
                        this.$('.paste-component').show()
                    }

                } else {
                    this.$('.paste-component').hide()
                }

            } else {
                this.$('.paste-component').hide();
            }
        },

        findXBlockElement: function(target) {
            return $(target).closest('.outline-subsection');
        },

        createPlaceholderElement: function() {
            return $('<li/>', {class: 'outline-item outline-unit has-warnings is-draggable'});
        },

        getURLRoot: function() {
            return this.model.urlRoot;
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
                rootLocator = this.model.id;

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

        onNewXBlock: function(xblockElement, scrollOffset, is_duplicate, data) {
            var useNewTextEditor = this.$('.xblock-header-primary').attr('use-new-editor-text'),
                useNewVideoEditor = this.$('.xblock-header-primary').attr('use-new-editor-video'),
                useVideoGalleryFlow = this.$('.xblock-header-primary').attr("use-video-gallery-flow"),
                useNewProblemEditor = this.$('.xblock-header-primary').attr('use-new-editor-problem');

            // find the block type in the locator if available
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
            // ViewUtils.setScrollOffset(xblockElement, scrollOffset);
            xblockElement.data('locator', data.locator);
            return this.refreshXBlock(xblockElement, true, is_duplicate);
        },

        /** The user has clicked on the "Paste Unit button" */
        pasteUnit(event) {
            // event.preventDefault();
            // Get the ID of the container (usually a unit/vertical) that we're pasting into:
            const parentElement = this.findXBlockElement(event.target);
            const parentLocator = parentElement.data('locator');
            // Create a placeholder XBlock while we're pasting:
            const $placeholderEl = $(this.createPlaceholderElement());
            const addComponentsPanel = $(event.target).closest('.paste-component').prev();

            // const listPanel = addComponentsPanel.prev();
            const listPanel = $(event.target).closest('.subsection-content').find('.list-units');

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
                    notices.push(() => new NotificationView.Confirmation({
                        title: gettext("New files were added to this course's Files & Uploads"),
                        message: (
                            gettext("The following required files were imported to this course:") +
                            " "  + newFiles.join(", ")
                        ),
                        closeIcon: true,
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

        highlightsXBlock: function() {
            var modal = CourseOutlineModalsFactory.getModal('highlights', this.model, {
                onSave: this.refresh.bind(this),
                xblockType: XBlockViewUtils.getXBlockType(
                    this.model.get('category'), this.parentView.model, true
                )
            });

            if (modal) {
                window.analytics.track('edx.bi.highlights.modal_open');
                modal.show();
            }
        },

        /**
         * If the new "Actions" menu is enabled, most actions like Configure,
         * Duplicate, Move, Delete, etc. are moved into this menu. For this
         * event, we just toggle displaying the menu.
         * @param {*} event 
         */
        showActionsMenu: function(event) {
            const showActionsButton = event.currentTarget;
            const subMenu = showActionsButton.parentElement.querySelector(".wrapper-nav-sub");
            // Code in 'base.js' normally handles toggling these dropdowns but since this one is
            // not present yet during the domReady event, we have to handle displaying it ourselves.
            subMenu.classList.toggle("is-shown");
            // if propagation is not stopped, the event will bubble up to the
            // body element, which will close the dropdown.
            event.stopPropagation();
        },

        addButtonActions: function(element) {
            XBlockOutlineView.prototype.addButtonActions.apply(this, arguments);
            element.find('.configure-button').click(function(event) {
                event.preventDefault();
                this.editXBlock();
            }.bind(this));
            element.find('.publish-button').click(function(event) {
                event.preventDefault();
                this.publishXBlock();
            }.bind(this));
            element.find('.highlights-button').on('click keydown', function(event) {
                if (event.type === 'click' || event.which === 13 || event.which === 32) {
                    event.preventDefault();
                    this.highlightsXBlock();
                }
            }.bind(this));
            element.find('.copy-button').click((event) => {
                event.preventDefault();
                this.copyXBlock();
            });
            element.find('.paste-component-button').click((event) => {
                event.preventDefault();
                this.pasteUnit(event);
            });
            element.find('.action-actions-menu').click((event) => {
                this.showActionsMenu(event);
            });
        },

        makeContentDraggable: function(element) {
            if ($(element).hasClass('outline-section')) {
                ContentDragger.makeDraggable(element, {
                    type: '.outline-section',
                    handleClass: '.section-drag-handle',
                    droppableClass: 'ol.list-sections',
                    parentLocationSelector: 'article.outline',
                    refresh: this.refreshWithCollapsedState.bind(this),
                    ensureChildrenRendered: this.ensureChildrenRendered.bind(this)
                });
            } else if ($(element).hasClass('outline-subsection')) {
                ContentDragger.makeDraggable(element, {
                    type: '.outline-subsection',
                    handleClass: '.subsection-drag-handle',
                    droppableClass: 'ol.list-subsections',
                    parentLocationSelector: 'li.outline-section',
                    refresh: this.refreshWithCollapsedState.bind(this),
                    ensureChildrenRendered: this.ensureChildrenRendered.bind(this)
                });
            } else if ($(element).hasClass('outline-unit')) {
                ContentDragger.makeDraggable(element, {
                    type: '.outline-unit',
                    handleClass: '.unit-drag-handle',
                    droppableClass: 'ol.list-units',
                    parentLocationSelector: 'li.outline-subsection',
                    refresh: this.refreshWithCollapsedState.bind(this),
                    ensureChildrenRendered: this.ensureChildrenRendered.bind(this)
                });
            }
        }
    });

    return CourseOutlineView;
}); // end define();
