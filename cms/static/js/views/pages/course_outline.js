/**
 * This page is used to show the user an outline of the course.
 */
define(["jquery", "underscore", "gettext", "js/views/pages/base_page", "js/views/utils/xblock_utils",
        "js/views/course_outline", "js/utils/drag_and_drop"],
    function ($, _, gettext, BasePage, XBlockViewUtils, CourseOutlineView, ContentDragger) {
        var CourseOutlinePage = BasePage.extend({
            // takes XBlockInfo as a model

            events: {
                "click .button-toggle-expand-collapse": "toggleExpandCollapse"
            },

            options: {
                collapsedClass: 'is-collapsed'
            },

            initialize: function() {
                var self = this;
                this.initialState = this.options.initialState;
                BasePage.prototype.initialize.call(this);
                this.$('.button-new').click(function(event) {
                    self.outlineView.handleAddEvent(event);
                });
                this.model.on('change', this.setCollapseExpandVisibility, this);
            },

            setCollapseExpandVisibility: function() {
                var has_content = this.hasContent(),
                    collapseExpandButton = $('.button-toggle-expand-collapse');
                if (has_content) {
                    collapseExpandButton.removeClass('is-hidden');
                } else {
                    collapseExpandButton.addClass('is-hidden');
                }
            },

            renderPage: function() {
                this.setCollapseExpandVisibility();
                this.outlineView = new CourseOutlineView({
                    el: this.$('.outline'),
                    model: this.model,
                    isRoot: true,
                    initialState: this.initialState
                });
                this.outlineView.render();
                this.outlineView.setViewState(this.initialState || {});

                // Section
                ContentDragger.makeDraggable(
                    '.outline-section',
                    '.section-drag-handle',
                    'ol.list-sections',
                    'article.outline'
                );
                // Subsection
                ContentDragger.makeDraggable(
                    '.outline-subsection',
                    '.subsection-drag-handle',
                    'ol.list-subsections',
                    'li.outline-section'
                );
                // Unit
                ContentDragger.makeDraggable(
                    '.outline-unit',
                    '.unit-drag-handle',
                    'ol.list-units',
                    'li.outline-subsection'
                );

                return $.Deferred().resolve().promise();
            },

            hasContent: function() {
                return this.model.hasChildren();
            },

            toggleExpandCollapse: function(event) {
                var toggleButton = this.$('.button-toggle-expand-collapse'),
                    collapse = toggleButton.hasClass('collapse-all');
                event.preventDefault();
                toggleButton.toggleClass('collapse-all expand-all');
                this.$('.list-sections > li').each(function(index, domElement) {
                    var element = $(domElement);
                    element.addClass(collapse ? 'is-collapsed' : 'is-expanded');
                    element.removeClass(collapse ? 'is-expanded' : 'is-collapsed');
                });
            }
        });

        return CourseOutlinePage;
    }); // end define();
