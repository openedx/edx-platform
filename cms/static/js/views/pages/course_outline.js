/**
 * This page is used to show the user an outline of the course.
 */
define(["jquery", "underscore", "gettext", "js/views/pages/base_page", "js/views/utils/xblock_utils",
        "js/views/course_outline"],
    function ($, _, gettext, BasePage, XBlockViewUtils, CourseOutlineView) {
        var CourseOutlinePage = BasePage.extend({
            // takes XBlockInfo as a model

            events: {
                "click .toggle-button-expand-collapse": "toggleExpandCollapse"
            },

            initialize: function() {
                var self = this;
                BasePage.prototype.initialize.call(this);
                this.$('.add-button').click(function(event) {
                    self.outlineView.handleAddEvent(event);
                });
            },

            renderPage: function() {
                this.outlineView = new CourseOutlineView({
                    el: this.$('.course-outline'),
                    model: this.model,
                    isRoot: true
                });
                this.outlineView.render();
                return $.Deferred().resolve().promise();
            },

            hasContent: function() {
                return this.model.get('child_info').children.length > 0;
            },

            toggleExpandCollapse: function(event) {
                var toggleButton = this.$('.toggle-button-expand-collapse'),
                    collapse = toggleButton.hasClass('collapse-all');
                event.preventDefault();
                toggleButton.toggleClass('collapse-all').toggleClass('expand-all');
                this.$('.course-outline  > ol > li').each(function(index, domElement) {
                    var element = $(domElement),
                        expandCollapseElement = element.find('.expand-collapse').first();
                    if (collapse) {
                        expandCollapseElement.removeClass('expand').addClass('collapse');
                        element.addClass('collapsed');
                    } else {
                        expandCollapseElement.addClass('expand').removeClass('collapse');
                        element.removeClass('collapsed');
                    }
                });
            }
        });

        return CourseOutlinePage;
    }); // end define();
