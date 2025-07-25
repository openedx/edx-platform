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
define(['jquery', 'underscore', 'js/views/xblock_outline', 'edx-ui-toolkit/js/utils/string-utils',
    'common/js/components/utils/view_utils', 'js/views/utils/xblock_utils',
    'js/models/xblock_outline_info', 'js/views/modals/course_outline_modals', 'js/utils/drag_and_drop',
    'common/js/components/views/feedback_notification', 'common/js/components/views/feedback_prompt',
    'js/views/utils/tagging_drawer_utils', 'js/views/tag_count', 'js/models/tag_count'],
function(
    $, _, XBlockOutlineView, StringUtils, ViewUtils, XBlockViewUtils,
    XBlockOutlineInfo, CourseOutlineModalsFactory, ContentDragger, NotificationView, PromptView,
    TaggingDrawerUtils, TagCountView, TagCountModel
) {
    var CourseOutlineView = XBlockOutlineView.extend({
        // takes XBlockOutlineInfo as a model

        templateName: 'course-outline',

        render: function() {
            var renderResult = XBlockOutlineView.prototype.render.call(this);
            this.makeContentDraggable(this.el);
            // Show/hide the paste button
            this.initializePasteButton(this.el);
            this.renderTagCount();
            return renderResult;
        },

        renderTagCount: function() {
            if (this.model.get('is_tagging_feature_disabled')) {
                return; // Tagging feature is disabled; don't initialize the tag count view.
            }
            const contentId = this.model.get('id');
            // Skip the course block since that is handled elsewhere in course_manage_tags
            if (contentId.includes('@course')) {
                return;
            }
            const tagCountsByBlock = this.model.get('tag_counts_by_block');
            const tagsCount = tagCountsByBlock !== undefined ? tagCountsByBlock[contentId] : 0;
            const tagCountElem = this.$(`.tag-count[data-locator="${contentId}"]`);
            var countModel = new TagCountModel({
                content_id: contentId,
                tags_count: tagsCount,
                course_authoring_url: this.model.get('course_authoring_url'),
            }, {parse: true});
            var tagCountView = new TagCountView({el: tagCountElem, model: countModel});
            tagCountView.setupMessageListener();
            tagCountView.render();
            tagCountElem.click((event) => {
                event.preventDefault();
                this.openManageTagsDrawer();
            });
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
            const clipboardEndpoint = '/api/content-staging/v1/clipboard/';
            // Start showing a "Copying" notification:
            ViewUtils.runOperationShowingMessage(gettext('Copying'), () => $.postJSON(
                clipboardEndpoint,
                {usage_key: this.model.get('id')}
            ).then((data) => {
                // const status = data.content?.status;
                const status = data.content && data.content.status;
                // ^ platform's old require.js/esprima breaks on newer syntax in some JS files but not all.
                if (status === 'ready') {
                    // The Unit has been copied and is ready to use.
                    this.clipboardManager.updateUserClipboard(data); // This will update the UI and notify other tabs
                    return data;
                } else if (status === 'loading') {
                    // The clipboard is being loaded asynchronously.
                    // Poll the endpoint until the copying process is complete:
                    const deferred = $.Deferred();
                    const checkStatus = () => {
                        $.getJSON(clipboardEndpoint, (pollData) => {
                            // const newStatus = pollData.content?.status;
                            const newStatus = pollData.content && pollData.content.status;
                            if (newStatus === 'ready') {
                                this.clipboardManager.updateUserClipboard(pollData);
                                deferred.resolve(pollData);
                            } else if (newStatus === 'loading') {
                                setTimeout(checkStatus, 1000);
                            } else {
                                deferred.reject();
                                throw new Error(`Unexpected clipboard status "${newStatus}" in successful API response.`);
                            }
                        });
                    };
                    setTimeout(checkStatus, 1000);
                    return deferred;
                } else {
                    throw new Error(`Unexpected clipboard status "${status}" in successful API response.`);
                }
            }));
        },

        initializePasteButton(element) {
            if ($(element).hasClass('outline-subsection')) {
                if (this.options.canEdit && this.clipboardManager) {
                    // We should have the user's clipboard status from CourseOutlinePage, whose clipboardManager manages
                    // the clipboard data on behalf of all the XBlocks in the outline.
                    this.refreshPasteButton(this.clipboardManager.userClipboard);
                    this.clipboardManager.addEventListener('update', (event) => {
                        this.refreshPasteButton(event.detail);
                    });
                } else {
                    this.$('.paste-component').hide();
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
                if (data.content.status === 'expired') {
                    // This has expired and can no longer be pasted.
                    this.$('.paste-component').hide();
                } else if (data.content.block_type === 'vertical') {
                    // This is suitable for pasting as a unit.
                    const detailsPopupEl = this.$('.clipboard-details-popup')[0];
                    // Only Units should have the paste button initialized
                    if (detailsPopupEl !== undefined) {
                        detailsPopupEl.querySelector('.detail-block-name').innerText = data.content.display_name;
                        detailsPopupEl.querySelector('.detail-block-type').innerText = data.content.block_type_display;
                        detailsPopupEl.querySelector('.detail-course-name').innerText = data.source_context_title;
                        if (data.source_edit_url) {
                            detailsPopupEl.setAttribute('href', data.source_edit_url);
                            detailsPopupEl.classList.remove('no-edit-link');
                        } else {
                            detailsPopupEl.setAttribute('href', '#');
                            detailsPopupEl.classList.add('no-edit-link');
                        }
                        this.$('.paste-component').show();
                    }
                } else {
                    this.$('.paste-component').hide();
                }
            } else {
                this.$('.paste-component').hide();
            }
        },

        createPlaceholderElementForPaste(category, componentDisplayName) {
            const nameStr = StringUtils.interpolate(gettext('Copy of "{componentDisplayName}"'), {componentDisplayName}, true);
            const el = document.createElement('li');
            el.classList.add('outline-item', 'outline-' + category, 'has-warnings', 'is-draggable');
            el.innerHTML = `
                <div class="${category}-header">
                    <h3 class="${category}-header-details" style="width: 50%">
                        <span class="${category}-title item-title">
                            ${nameStr}
                        </span>
                    </h3>
                    <div class="${category}-header-actions" style="width: 50%; text-align: right;">
                        <ul class="actions-list nav-dd ui-right">
                            <li class="action-item">
                                <span class="icon fa fa-spinner fa-pulse fa-spin" aria-hidden="true"></span>
                            </li>
                        </ul>
                    </div>
                </div>
            `;
            return $(el);
        },

        /** The user has clicked on the "Paste Unit button" */
        pasteUnit(event) {
            // event.preventDefault();
            // Get the ID of the parent container (a subsection if we're pasting a unit/vertical) that we're pasting into
            const $parentElement = $(event.target).closest('.outline-item');
            const parentLocator = $parentElement.data('locator');
            // Get the display name of what we're pasting:
            const displayName = $(event.target).closest('.paste-component').find('.detail-block-name').text();
            // Create a placeholder XBlock while we're pasting:
            const $placeholderEl = this.createPlaceholderElementForPaste('unit', displayName);
            const $listPanel = $(event.target).closest('.outline-content').children('ol').first();
            $listPanel.append($placeholderEl);

            // Start showing a "Pasting" notification:
            ViewUtils.runOperationShowingMessage(gettext('Pasting'), () => $.postJSON(this.model.urlRoot + '/', {
                parent_locator: parentLocator,
                staged_content: 'clipboard',
            }).then((data) => {
                this.refresh(); // Update this and replace the placeholder with the actual pasted unit.
                return data;
            }).fail(() => {
                $placeholderEl.remove();
            })).done((data) => {
                const {
                    conflicting_files: conflictingFiles,
                    error_files: errorFiles,
                    new_files: newFiles,
                } = data.static_file_notices;

                const notices = [];
                if (errorFiles.length) {
                    notices.push((next) => new PromptView.Error({
                        title: gettext('Some errors occurred'),
                        message: (
                            gettext('The following required files could not be added to the course:')
                            + ' ' + errorFiles.join(', ')
                        ),
                        actions: {primary: {text: gettext('OK'), click: (x) => { x.hide(); next(); }}},
                    }));
                }
                if (conflictingFiles.length) {
                    notices.push((next) => new PromptView.Warning({
                        title: gettext('You may need to update a file(s) manually'),
                        message: (
                            gettext(
                                'The following files already exist in this course but don\'t match the '
                                + 'version used by the component you pasted:'
                            ) + ' ' + conflictingFiles.join(', ')
                        ),
                        actions: {primary: {text: gettext('OK'), click: (x) => { x.hide(); next(); }}},
                    }));
                }
                if (newFiles.length) {
                    notices.push(() => new NotificationView.Info({
                        title: gettext('New file(s) added to Files & Uploads.'),
                        message: (
                            gettext('The following required files were imported to this course:')
                            + ' ' + newFiles.join(', ')
                        ),
                        actions: {
                            primary: {
                                text: gettext('View files'),
                                click: function(notification) {
                                    const article = document.querySelector('[data-course-assets]');
                                    const assetsUrl = $(article).attr('data-course-assets');
                                    window.location.href = assetsUrl;
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
                    };
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

        subsectionShareLinkXBlock: function() {
            var modal = CourseOutlineModalsFactory.getModal('subsection_share_link', this.model, {
                onSave: this.refresh.bind(this),
                xblockType: XBlockViewUtils.getXBlockType(
                    this.model.get('category'), this.parentView.model, true
                )
            });

            if (modal) {
                modal.show();
            }
        },

        /**
         * If the new "Actions" menu is enabled, most actions like Configure,
         * Duplicate, Move, Delete, etc. are moved into this menu. For this
         * event, we just toggle displaying the menu.
         */
        showActionsMenu(event) {
            const showActionsButton = event.currentTarget;
            const subMenu = showActionsButton.parentElement.querySelector('.wrapper-nav-sub');

            // Close all open dropdowns
            const elements = document.querySelectorAll('li.action-item.action-actions-menu.nav-item');
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

        openManageTagsDrawer() {
            const taxonomyTagsWidgetUrl = this.model.get('taxonomy_tags_widget_url');
            const contentId = this.model.get('id');
            TaggingDrawerUtils.openDrawer(taxonomyTagsWidgetUrl, contentId);
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
            element.find('.subsection-share-link-button').click(function(event) {
                event.preventDefault();
                this.subsectionShareLinkXBlock();
            }.bind(this));
            element.find('.copy-button').click((event) => {
                event.preventDefault();
                this.copyXBlock();
            });
            element.find('.manage-tags-button').click((event) => {
                event.preventDefault();
                this.openManageTagsDrawer();
            });
            element.find('.paste-component-button').click((event) => {
                event.preventDefault();
                this.pasteUnit(event);
            });
            element.find('.show-actions-menu-button').click((event) => {
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
