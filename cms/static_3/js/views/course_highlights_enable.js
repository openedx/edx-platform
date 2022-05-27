define([
    'jquery', 'underscore', 'backbone', 'js/views/utils/xblock_utils', 'js/utils/templates',
    'js/views/modals/course_outline_modals', 'edx-ui-toolkit/js/utils/html-utils'],
    function(
        $, _, Backbone, XBlockViewUtils, TemplateUtils, CourseOutlineModalsFactory, HtmlUtils
    ) {
        'use strict';
        var CourseHighlightsEnableView = Backbone.View.extend({
            events: {
                'click button.status-highlights-enabled-value': 'handleEnableButtonPress',
                'keypress button.status-highlights-enabled-value': 'handleEnableButtonPress'
            },

            initialize: function() {
                this.template = TemplateUtils.loadTemplate('course-highlights-enable');
            },

            handleEnableButtonPress: function(event) {
                if (event.type === 'click' || event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    this.highlightsEnableXBlock();
                }
            },

            highlightsEnableXBlock: function() {
                var modal = CourseOutlineModalsFactory.getModal('highlights_enable', this.model, {
                    onSave: this.refresh.bind(this),
                    xblockType: XBlockViewUtils.getXBlockType(
                        this.model.get('category')
                    )
                });

                if (modal) {
                    window.analytics.track('edx.bi.highlights_enable.modal_open');
                    modal.show();
                }
            },

            refresh: function() {
                this.model.fetch({
                    success: this.render.bind(this)
                });
            },

            render: function() {
                var html = this.template(this.model.attributes);
                HtmlUtils.setHtml(this.$el, HtmlUtils.HTML(html));
                return this;
            }
        });

        return CourseHighlightsEnableView;
    }
);
