define(
    ['jquery', 'underscore', 'backbone', 'js/views/baseview', 'edx-ui-toolkit/js/utils/html-utils',
        'js/views/previous_video_upload', 'text!templates/previous-video-upload-list.underscore'],
    function($, _, Backbone, BaseView, HtmlUtils, PreviousVideoUploadView, previousVideoUploadListTemplate) {
        'use strict';
        var PreviousVideoUploadListView = BaseView.extend({
            tagName: 'section',
            className: 'wrapper-assets',

            initialize: function(options) {
                this.template = HtmlUtils.template(previousVideoUploadListTemplate);
                this.encodingsDownloadUrl = options.encodingsDownloadUrl;
                this.videoImageUploadEnabled = options.videoImageSettings.video_image_upload_enabled;
                this.itemViews = this.collection.map(function(model) {
                    return new PreviousVideoUploadView({
                        videoImageUploadURL: options.videoImageUploadURL,
                        defaultVideoImageURL: options.defaultVideoImageURL,
                        videoHandlerUrl: options.videoHandlerUrl,
                        videoImageSettings: options.videoImageSettings,
                        videoTranscriptSettings: options.videoTranscriptSettings,
                        model: model,
                        transcriptAvailableLanguages: options.transcriptAvailableLanguages,
                        videoSupportedFileFormats: options.videoSupportedFileFormats
                    });
                });
            },

            render: function() {
                var $el = this.$el,
                    $tabBody;

                HtmlUtils.setHtml(
                    this.$el,
                    this.template({
                        encodingsDownloadUrl: this.encodingsDownloadUrl,
                        videoImageUploadEnabled: this.videoImageUploadEnabled
                    })
                );

                $tabBody = $el.find('.js-table-body');
                _.each(this.itemViews, function(view) {
                    $tabBody.append(view.render().$el);
                });
                return this;
            }
        });

        return PreviousVideoUploadListView;
    }
);
