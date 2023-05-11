define([
    'jquery',
    'underscore',
    'backbone',
    'js/views/utils/xblock_utils',
    'js/utils/templates',
    'js/views/modals/course_outline_modals',
    'edx-ui-toolkit/js/utils/html-utils',
], function($, _, Backbone, XBlockViewUtils, TemplateUtils, CourseOutlineModalsFactory, HtmlUtils) {
    'use strict';

    var CourseVideoSharingEnableView = Backbone.View.extend({
        events: {
            'change #video-sharing-configuration-options': 'handleVideoSharingConfigurationChange',
        },

        initialize: function() {
            this.template = TemplateUtils.loadTemplate('course-video-sharing-enable');
        },

        getRequestData: function(value) {
            return {
                metadata: {
                    video_sharing_options: value,
                },
            };
        },

        handleVideoSharingConfigurationChange: function(event) {
            if (event.type === 'change') {
                event.preventDefault();
                this.updateVideoSharingConfiguration(event.target.value);
                this.trackVideoSharingConfigurationChange(event.target.value);
            }
        },

        updateVideoSharingConfiguration: function(value) {
            XBlockViewUtils.updateXBlockFields(this.model, this.getRequestData(value), {
                success: this.refresh.bind(this)
            });
        },

        trackVideoSharingConfigurationChange: function(value) {
            window.analytics.track(
                'edx.social.video_sharing_options.changed',
                {
                    course_id: this.model.id,
                    video_sharing_options: value
                }
            );
        },

        refresh: function() {
            this.model.fetch({
                success: this.render.bind(this),
            });
        },

        render: function() {
            var html = this.template(this.model.attributes);
            HtmlUtils.setHtml(this.$el, HtmlUtils.HTML(html));
            return this;
        },
    });

    return CourseVideoSharingEnableView;
});
