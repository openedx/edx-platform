define(
    [
        'underscore',
        'gettext',
        'cms/static/js/utils/date_utils',
        'cms/static/js/views/baseview',
        'cms/static/common/js/components/views/feedback_prompt',
        'cms/static/common/js/components/views/feedback_notification',
        'cms/static/js/views/video_thumbnail',
        'cms/static/common/js/components/utils/view_utils',
        'common/static/edx-ui-toolkit/js/utils/html-utils',
        'text!cms/static/templates/previous-video-upload.underscore'
    ],
    function(_, gettext, DateUtils, BaseView, PromptView, NotificationView, VideoThumbnailView, ViewUtils, HtmlUtils,
             previousVideoUploadTemplate) {
        'use strict';

        var PreviousVideoUploadView = BaseView.extend({
            tagName: 'div',

            className: 'video-row',

            events: {
                'click .remove-video-button.action-button': 'removeVideo'
            },

            initialize: function(options) {
                this.template = HtmlUtils.template(previousVideoUploadTemplate);
                this.videoHandlerUrl = options.videoHandlerUrl;
                this.videoImageUploadEnabled = options.videoImageSettings.video_image_upload_enabled;

                if (this.videoImageUploadEnabled) {
                    this.videoThumbnailView = new VideoThumbnailView({
                        model: this.model,
                        imageUploadURL: options.videoImageUploadURL,
                        defaultVideoImageURL: options.defaultVideoImageURL,
                        videoImageSettings: options.videoImageSettings
                    });
                }
            },

            render: function() {
                var renderedAttributes = {
                    videoImageUploadEnabled: this.videoImageUploadEnabled,
                    created: DateUtils.renderDate(this.model.get('created')),
                    status: this.model.get('status')
                };
                HtmlUtils.setHtml(
                    this.$el,
                    this.template(
                        _.extend({}, this.model.attributes, renderedAttributes)
                    )
                );

                if (this.videoImageUploadEnabled) {
                    this.videoThumbnailView.setElement(this.$('.thumbnail-col')).render();
                }
                return this;
            },

            removeVideo: function(event) {
                var videoView = this;
                event.preventDefault();

                ViewUtils.confirmThenRunOperation(
                    gettext('Are you sure you want to remove this video from the list?'),
                    gettext('Removing a video from this list does not affect course content. Any content that uses a previously uploaded video ID continues to display in the course.'),  // eslint-disable-line max-len
                    gettext('Remove'),
                    function() {
                        ViewUtils.runOperationShowingMessage(
                            gettext('Removing'),
                            function() {
                                return $.ajax({
                                    url: videoView.videoHandlerUrl + '/' + videoView.model.get('edx_video_id'),
                                    type: 'DELETE'
                                }).done(function() {
                                    videoView.remove();
                                });
                            }
                        );
                    }
                );
            }
        });

        return PreviousVideoUploadView;
    }
);
