define([
    'jquery', 'underscore', 'backbone', 'js/utils/templates',
    'edx-ui-toolkit/js/utils/html-utils', 'js/views/utils/tagging_drawer_utils',
    'js/views/tag_count', 'js/models/tag_count'],
function(
    $, _, Backbone, TemplateUtils, HtmlUtils, TaggingDrawerUtils, TagCountView, TagCountModel
) {
    'use strict';

    var CourseManageTagsView = Backbone.View.extend({
        events: {
            'click .manage-tags-button': 'openManageTagsDrawer',
        },

        initialize: function() {
            this.template = TemplateUtils.loadTemplate('course-manage-tags');
            this.courseId = course.id;
        },

        openManageTagsDrawer: function(event) {
            const taxonomyTagsWidgetUrl = this.model.get('taxonomy_tags_widget_url');
            const contentId = this.courseId;
            TaggingDrawerUtils.openDrawer(taxonomyTagsWidgetUrl, contentId);
        },

        renderTagCount: function() {
            const contentId = this.courseId;
            const tagCountsForCourse = this.model.get('course_tags_count');
            const tagsCount = tagCountsForCourse !== undefined ? tagCountsForCourse[contentId] : 0;
            var countModel = new TagCountModel({
                content_id: contentId,
                tags_count: tagsCount,
                course_authoring_url: this.model.get('course_authoring_url'),
            }, {parse: true});
            var tagCountView = new TagCountView({el: this.$('.tag-count'), model: countModel});
            tagCountView.setupMessageListener();
            tagCountView.render();
            this.$('.tag-count').click((event) => {
                event.preventDefault();
                this.openManageTagsDrawer();
            });
        },

        render: function() {
            var html = this.template(this.model.attributes);
            HtmlUtils.setHtml(this.$el, HtmlUtils.HTML(html));
            this.renderTagCount();
            return this;
        }
    });

    return CourseManageTagsView;
}
);
