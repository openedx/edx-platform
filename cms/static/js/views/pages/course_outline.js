/**
 * This page is used to show the user an outline of the course.
 */
define(["jquery", "underscore", "gettext", "js/views/pages/base_page", "js/views/xblock_outline"],
    function ($, _, gettext, BasePage, XBlockOutlineView) {
        var CourseOutlinePage = BasePage.extend({
            // takes XBlockInfo as a model

            view: 'container_preview',

            initialize: function() {
                BasePage.prototype.initialize.call(this);
            },

            renderPage: function() {
                if (this.hasContent()) {
                    this.outlineView = new XBlockOutlineView({
                        el: this.$('.courseware-overview'),
                        model: this.model
                    });
                    this.outlineView.render();
                }
                return $.Deferred().resolve().promise();
            },

            hasContent: function() {
                return this.model.get('children').length > 0;
            }
        });

        return CourseOutlinePage;
    }); // end define();
