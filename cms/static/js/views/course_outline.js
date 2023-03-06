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

        render: function() {
            var renderResult = XBlockOutlineView.prototype.render.call(this);
            this.makeContentDraggable(this.el);
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
