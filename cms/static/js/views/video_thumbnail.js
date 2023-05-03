define(
    ['underscore', 'gettext', 'moment', 'js/utils/date_utils', 'js/views/baseview',
        'common/js/components/utils/view_utils', 'edx-ui-toolkit/js/utils/html-utils',
        'edx-ui-toolkit/js/utils/string-utils', 'text!templates/video-thumbnail.underscore',
        'text!templates/video-thumbnail-error.underscore'],
    function(_, gettext, moment, DateUtils, BaseView, ViewUtils, HtmlUtils, StringUtils, VideoThumbnailTemplate,
        VideoThumbnailErrorTemplate) {
        'use strict';

        var VideoThumbnailView = BaseView.extend({

            events: {
                'click .thumbnail-wrapper': 'chooseFile',
                'mouseover .thumbnail-wrapper': 'showHoverState',
                'mouseout .thumbnail-wrapper': 'hideHoverState',
                'focus .thumbnail-wrapper': 'showHoverState',
                'blur .thumbnail-wrapper': 'hideHoverState'
            },

            initialize: function(options) {
                this.template = HtmlUtils.template(VideoThumbnailTemplate);
                this.thumbnailErrorTemplate = HtmlUtils.template(VideoThumbnailErrorTemplate);
                this.imageUploadURL = options.imageUploadURL;
                this.defaultVideoImageURL = options.defaultVideoImageURL;
                this.action = this.model.get('course_video_image_url') ? 'edit' : 'upload';
                this.videoImageSettings = options.videoImageSettings;
                this.actionsInfo = {
                    upload: {
                        name: 'upload',
                        icon: '',
                        text: gettext('Add Thumbnail')
                    },
                    edit: {
                        name: 'edit',
                        actionText: gettext('Edit Thumbnail'),
                        icon: '<span class="icon fa fa-pencil" aria-hidden="true"></span>',
                        text: HtmlUtils.interpolateHtml(
                            // Translators: This is a 2 part text which tells the image requirements.
                            gettext('{InstructionsSpanStart}{videoImageResoultion}{lineBreak} {videoImageSupportedFileFormats}{spanEnd}'),   // eslint-disable-line max-len
                            {
                                videoImageResoultion: this.getVideoImageResolution(),
                                videoImageSupportedFileFormats: this.getVideoImageSupportedFileFormats().humanize,
                                lineBreak: HtmlUtils.HTML('<br>'),
                                InstructionsSpanStart: HtmlUtils.HTML('<span class="requirements-instructions">'),
                                spanEnd: HtmlUtils.HTML('</span>')
                            }
                        ).toString()
                    },
                    error: {
                        name: 'error',
                        icon: '',
                        text: gettext('Image upload failed')
                    },
                    progress: {
                        name: 'progress-action',
                        icon: '<span class="icon fa fa-spinner fa-pulse fa-spin" aria-hidden="true"></span>',
                        text: gettext('Uploading')
                    },
                    requirements: {
                        name: 'requirements',
                        icon: '',
                        text: HtmlUtils.interpolateHtml(
                            // Translators: This is a 3 part text which tells the image requirements.
                            gettext('{ReqTextSpanStart}Requirements{spanEnd}{lineBreak}{InstructionsSpanStart}{videoImageResoultion}{lineBreak} {videoImageSupportedFileFormats}{spanEnd}'),   // eslint-disable-line max-len
                            {
                                videoImageResoultion: this.getVideoImageResolution(),
                                videoImageSupportedFileFormats: this.getVideoImageSupportedFileFormats().humanize,
                                lineBreak: HtmlUtils.HTML('<br>'),
                                ReqTextSpanStart: HtmlUtils.HTML('<span class="requirements-text">'),
                                InstructionsSpanStart: HtmlUtils.HTML('<span class="requirements-instructions">'),
                                spanEnd: HtmlUtils.HTML('</span>')
                            }
                        ).toString()
                    }
                };

                _.bindAll(
                    this, 'render', 'chooseFile', 'imageSelected', 'imageUploadSucceeded', 'imageUploadFailed',
                    'showHoverState', 'hideHoverState'
                );
            },

            render: function() {
                HtmlUtils.setHtml(
                    this.$el,
                    this.template({
                        action: this.action,
                        imageAltText: this.getImageAltText(),
                        videoId: this.model.get('edx_video_id'),
                        actionInfo: this.actionsInfo[this.action],
                        thumbnailURL: this.model.get('course_video_image_url') || this.defaultVideoImageURL,
                        duration: this.getDuration(this.model.get('duration')),
                        videoImageSupportedFileFormats: this.getVideoImageSupportedFileFormats(),
                        videoImageMaxSize: this.getVideoImageMaxSize(),
                        videoImageResolution: this.getVideoImageResolution()
                    })
                );
                this.hideHoverState();
                return this;
            },

            getVideoImageSupportedFileFormats: function() {
                var supportedFormats = _.reject(_.keys(this.videoImageSettings.supported_file_formats), function(item) {
                    // Don't show redundant extensions to end user.
                    return item === '.bmp2' || item === '.jpeg';
                }).sort();
                return {
                    humanize: supportedFormats.slice(0, -1).join(', ') + ' or ' + supportedFormats.slice(-1),
                    machine: _.values(this.videoImageSettings.supported_file_formats)
                };
            },

            getVideoImageMaxSize: function() {
                return {
                    humanize: this.videoImageSettings.max_size / (1024 * 1024) + ' MB',
                    machine: this.videoImageSettings.max_size
                };
            },

            getVideoImageMinSize: function() {
                return {
                    humanize: this.videoImageSettings.min_size / 1024 + ' KB',
                    machine: this.videoImageSettings.min_size
                };
            },

            getVideoImageResolution: function() {
                return StringUtils.interpolate(
                    // Translators: message will be like 1280x720 pixels
                    gettext('{maxWidth}x{maxHeight} pixels'),
                    {maxWidth: this.videoImageSettings.max_width, maxHeight: this.videoImageSettings.max_height}
                );
            },

            getImageAltText: function() {
                return StringUtils.interpolate(
                    // Translators: message will be like Thumbnail for Arrow.mp4
                    gettext('Thumbnail for {videoName}'),
                    {videoName: this.model.get('client_video_id')}
                );
            },

            getSRText: function() {
                return StringUtils.interpolate(
                    // Translators: message will be like Add Thumbnail - Arrow.mp4
                    gettext('Add Thumbnail - {videoName}'),
                    {videoName: this.model.get('client_video_id')}
                );
            },

            getDuration: function(durationSeconds) {
                if (durationSeconds <= 0) {
                    return null;
                }

                return {
                    humanize: this.getDurationTextHuman(durationSeconds),
                    machine: this.getDurationTextMachine(durationSeconds)
                };
            },

            getDurationTextHuman: function(durationSeconds) {
                var humanize = this.getHumanizeDuration(durationSeconds);

                // This case is specifically to handle values between 0 and 1 seconds excluding upper bound
                if (humanize.length === 0) {
                    return '';
                }

                return StringUtils.interpolate(
                    // Translators: humanizeDuration will be like 10 minutes, an hour and 20 minutes etc
                    gettext('Video duration is {humanizeDuration}'),
                    {
                        humanizeDuration: humanize
                    }
                );
            },

            getHumanizeDuration: function(durationSeconds) {
                var minutes,
                    seconds,
                    minutesText = null,
                    secondsText = null;

                minutes = Math.trunc(moment.duration(durationSeconds, 'seconds').asMinutes());
                seconds = moment.duration(durationSeconds, 'seconds').seconds();

                if (minutes) {
                    minutesText = minutes > 1 ? gettext('minutes') : gettext('minute');
                    minutesText = StringUtils.interpolate(
                        // Translators: message will be like 15 minutes, 1 minute
                        gettext('{minutes} {unit}'),
                        {minutes: minutes, unit: minutesText}
                    );
                }

                if (seconds) {
                    secondsText = seconds > 1 ? gettext('seconds') : gettext('second');
                    secondsText = StringUtils.interpolate(
                        // Translators: message will be like 20 seconds, 1 second
                        gettext('{seconds} {unit}'),
                        {seconds: seconds, unit: secondsText}
                    );
                }

                // Translators: `and` will be used to combine both miuntes and seconds like `13 minutes and 45 seconds`
                return _.filter([minutesText, secondsText]).join(gettext(' and '));
            },

            getDurationTextMachine: function(durationSeconds) {
                var minutes = Math.floor(durationSeconds / 60),
                    seconds = Math.floor(durationSeconds - minutes * 60);
                return minutes + ':' + (seconds < 10 ? '0' : '') + seconds;
            },

            chooseFile: function() {
                this.$('.upload-image-input').fileupload({
                    url: this.imageUploadURL + '/' + encodeURIComponent(this.model.get('edx_video_id')),
                    add: this.imageSelected,
                    done: this.imageUploadSucceeded,
                    fail: this.imageUploadFailed
                });
            },

            imageSelected: function(event, data) {
                var errorMessage;
                // If an error is already present above the video element, remove it.
                this.clearErrorMessage(this.model.get('edx_video_id'));

                errorMessage = this.validateImageFile(data.files[0]);
                if (!errorMessage) {
                    // Do not trigger global AJAX error handler
                    data.global = false;    // eslint-disable-line no-param-reassign
                    this.readMessages([gettext('Video image upload started')]);
                    this.showUploadInProgressMessage();
                    data.submit();
                } else {
                    this.showErrorMessage(errorMessage);
                }
            },

            imageUploadSucceeded: function(event, data) {
                this.action = 'edit';
                this.setActionInfo(this.action, false);
                this.$('img').attr('src', data.result.image_url);
                this.readMessages([gettext('Video image upload completed')]);
            },

            imageUploadFailed: function(event, data) {
                var errorText = JSON.parse(data.jqXHR.responseText).error;
                this.showErrorMessage(errorText);
            },

            showUploadInProgressMessage: function() {
                this.action = 'progress';
                this.setActionInfo(this.action, true);
            },

            showHoverState: function() {
                if (this.action === 'upload') {
                    this.setActionInfo('requirements', true, this.getSRText());
                } else if (this.action === 'edit') {
                    this.setActionInfo(this.action, true);
                }
                this.$('.thumbnail-wrapper').addClass('focused');
            },

            hideHoverState: function() {
                if (this.action === 'upload') {
                    this.setActionInfo(this.action, true);
                } else if (this.action === 'edit') {
                    this.setActionInfo(this.action, false);
                }
                this.$('.thumbnail-wrapper').removeClass('focused');
            },

            setActionInfo: function(action, showText, additionalSRText) {
                var hasError = this.$('.thumbnail-wrapper').hasClass('error');
                this.$('.thumbnail-action').toggle(showText);
                HtmlUtils.setHtml(
                    this.$('.thumbnail-action .action-icon'),
                    HtmlUtils.HTML(this.actionsInfo[action].icon)
                );
                HtmlUtils.setHtml(
                    this.$('.thumbnail-action .action-text'),
                    HtmlUtils.HTML(this.actionsInfo[action].text)
                );
                this.$('.thumbnail-action .action-text-sr').text(additionalSRText || '');
                this.$('.thumbnail-wrapper').attr('class', 'thumbnail-wrapper {action}'.replace('{action}', action));
                this.$('.thumbnail-action .action-icon')
                    .attr('class', 'action-icon {action}'.replace('{action}', action));

                // Add error class if it was already present.
                if (hasError) {
                    this.$('.thumbnail-wrapper').addClass('error');
                }

                // Don't show edit-container layout on progress action.
                if (action === 'progress') {
                    this.$('.thumbnail-action .edit-container').toggle(false);
                } else if (action === 'edit') {
                    this.$('.thumbnail-action .edit-container').toggle(true);
                    HtmlUtils.setHtml(
                        this.$('.thumbnail-action .edit-container .action-icon'),
                        HtmlUtils.HTML(this.actionsInfo[action].icon)
                    );
                    HtmlUtils.setHtml(
                        this.$('.thumbnail-action .edit-container .edit-action-text'),
                        HtmlUtils.HTML(this.actionsInfo[action].actionText)
                    );
                }
            },

            validateImageFile: function(imageFile) {
                var errorMessage = '';

                if (!_.contains(this.getVideoImageSupportedFileFormats().machine, imageFile.type)) {
                    errorMessage = StringUtils.interpolate(
                        // Translators: supportedFileFormats will be like .bmp, gif, .jpg or .png.
                        gettext(
                            'This image file type is not supported. Supported file types are {supportedFileFormats}.'
                        ),
                        {
                            supportedFileFormats: this.getVideoImageSupportedFileFormats().humanize
                        }
                    );
                } else if (imageFile.size > this.getVideoImageMaxSize().machine) {
                    errorMessage = StringUtils.interpolate(
                        // Translators: maxFileSizeInMB will be like 2 MB.
                        gettext('The selected image must be smaller than {maxFileSizeInMB}.'),
                        {
                            maxFileSizeInMB: this.getVideoImageMaxSize().humanize
                        }
                    );
                } else if (imageFile.size < this.getVideoImageMinSize().machine) {
                    errorMessage = StringUtils.interpolate(
                        // Translators: minFileSizeInKB will be like 2 KB.
                        gettext('The selected image must be larger than {minFileSizeInKB}.'),
                        {
                            minFileSizeInKB: this.getVideoImageMinSize().humanize
                        }
                    );
                }

                return errorMessage;
            },

            clearErrorMessage: function(videoId) {
                var $thumbnailWrapperEl = $('.thumbnail-error-wrapper[data-video-id="' + videoId + '"]');
                if ($thumbnailWrapperEl.length) {
                    $thumbnailWrapperEl.remove();
                }
                // Remove error class from thumbnail wrapper as well.
                $('.thumbnail-wrapper').removeClass('error');
            },

            showErrorMessage: function(errorText) {
                var videoId = this.model.get('edx_video_id'),
                    $parentRowEl = $(this.$el.parent());

                // If image url is not this.defaultVideoImageURL then it means image is uploaded
                // so we should treat it as edit action otherwise default upload action.
                this.action = this.$('.thumbnail-wrapper img').attr('src') !== this.defaultVideoImageURL
                    ? 'edit' : 'upload';
                this.setActionInfo(this.action, true);
                this.readMessages([gettext('Could not upload the video image file'), errorText]);

                errorText = gettext('Image upload failed. ') + errorText;   // eslint-disable-line no-param-reassign
                // Add error wrapper html to current video element row.
                $parentRowEl.before(    // xss-lint: disable=javascript-jquery-insertion
                    HtmlUtils.ensureHtml(
                        this.thumbnailErrorTemplate({videoId: videoId, errorText: errorText})
                    ).toString()
                );
                this.$el.find('.thumbnail-wrapper').addClass('error');
            },

            readMessages: function(messages) {
                if ($(window).prop('SR') !== undefined) {
                    $(window).prop('SR').readTexts(messages);
                }
            }
        });

        return VideoThumbnailView;
    }
);
