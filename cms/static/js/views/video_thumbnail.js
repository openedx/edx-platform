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
                        icon: '',
                        text: gettext('Add Thumbnail')
                    },
                    edit: {
                        icon: '<span class="icon fa fa-pencil" aria-hidden="true"></span>',
                        text: gettext('Edit Thumbnail')
                    },
                    error: {
                        icon: '',
                        text: gettext('Image upload failed')
                    },
                    progress: {
                        icon: '<span class="icon fa fa-spinner fa-pulse fa-spin" aria-hidden="true"></span>',
                        text: gettext('Uploading')
                    },
                    requirements: {
                        icon: '',
                        text: HtmlUtils.interpolateHtml(
                            // Translators: This is a 3 part text which tells the image requirements.
                            gettext('{ReqTextSpanStart}Image requirements{spanEnd}{lineBreak}{InstructionsSpanStart}{videoImageResoultion}{lineBreak} {videoImageSupportedFileFormats}{spanEnd}'),   // eslint-disable-line max-len
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

                // When we had error, focused effect was not wearing off after hover out.
                // Add focused class to all rows except rows having error.
                if (!$(this.$el.parent()).hasClass('has-thumbnail-error')) {
                    this.$('.thumbnail-wrapper').addClass('focused');
                }
            },

            hideHoverState: function() {
                if (this.action === 'upload') {
                    this.setActionInfo(this.action, true);
                } else if (this.action === 'edit') {
                    this.setActionInfo(this.action, false);
                }
            },

            setActionInfo: function(action, showText, additionalSRText) {
                this.$('.thumbnail-action').toggle(showText);

                // In case of error, we don't want to show any icon on the image.
                if (action === 'error') {
                    HtmlUtils.setHtml(
                        this.$('.thumbnail-action .action-icon'),
                        HtmlUtils.HTML('')
                    );
                } else {
                    HtmlUtils.setHtml(
                        this.$('.thumbnail-action .action-icon'),
                        HtmlUtils.HTML(this.actionsInfo[action].icon)
                    );
                }
                HtmlUtils.setHtml(
                    this.$('.thumbnail-action .action-text'),
                    HtmlUtils.HTML(this.actionsInfo[action].text)
                );
                this.$('.thumbnail-action .action-text-sr').text(additionalSRText || '');
                this.$('.thumbnail-wrapper').attr('class', 'thumbnail-wrapper {action}'.replace('{action}', action));
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
            },

            showErrorMessage: function(errorText) {
                var videoId = this.model.get('edx_video_id'),
                    $parentRowEl = $(this.$el.parent());

                this.action = 'error';
                this.setActionInfo(this.action, true);
                this.readMessages([gettext('Could not upload the video image file'), errorText]);

                // Add css classes so as to distinguish.
                $parentRowEl.addClass('has-thumbnail-error thumbnail-error');

                // We need to update data attr in DOM too so as to find our element on hover.
                $parentRowEl.attr('data-video-id', videoId);

                // Add error wrapper html before current video element row.
                $parentRowEl.before(    // safe-lint: disable=javascript-jquery-insertion
                   HtmlUtils.ensureHtml(
                       this.thumbnailErrorTemplate({videoId: videoId, errorText: errorText})
                   ).toString()
                );

                // We need to treat error and error throwing row as one.
                // Refresh table rows to reflect error row.
                this.refreshVideoTableRowClasses();

                // To treat current row and it's error row as one on hover,
                // we add hover effect to both rows, even if it is hovered on only one row, thus, giving us
                // the combined one row feel.
                $('.thumbnail-error[data-video-id="' + videoId + '"]').hover(function() {
                    $('.thumbnail-error[data-video-id="' + videoId + '"]').toggleClass('blue-l5');
                });
            },

            /*
            Refresh video table classes.

            This method treats row and their corresponsing error rows as one, for that to achieve we need to reset
            table row even odd colors.
            */
            refreshVideoTableRowClasses: function() {
                var savedClass, // this class will be applied to the row corresponding to error row.
                    oddRowClass = 'white',
                    evenRowClass = 'gray-l6';

                $('.view-video-uploads .assets-table .js-table-body tr').each(function(index) {
                    var currentRowClass;

                    // Decide current iterated row is even or odd.
                    if (index % 2 === 0) {
                        currentRowClass = evenRowClass;
                    } else {
                        currentRowClass = oddRowClass;
                    }

                    // If the row is error row, save it's class so that it can be applied to it's corresponding row.
                    if ($(this).hasClass('thumbnail-error-wrapper')) {
                        savedClass = currentRowClass;
                    }

                    // If current iterated row is the row which generated error
                    // Apply the class same as it's corresponding error row. The class was saved.
                    if ($(this).hasClass('has-thumbnail-error')) {
                        // First remove previously added classes.
                        $(this).removeClass(evenRowClass);
                        $(this).removeClass(oddRowClass);

                        // Apply new class now.
                        $(this).addClass(savedClass);

                        // Now after the saved class, swap even odd row classes.
                        if (currentRowClass === oddRowClass) {
                            oddRowClass = evenRowClass;
                            evenRowClass = currentRowClass;
                        } else {
                            evenRowClass = oddRowClass;
                            oddRowClass = currentRowClass;
                        }
                        // Reset the saved class after it has been applied.
                        savedClass = '';
                    } else {
                        // For all simple rows, first remove classes if added
                        $(this).removeClass(evenRowClass);
                        $(this).removeClass(oddRowClass);

                        // then add the class based on it's rows.
                        $(this).addClass(currentRowClass);
                    }
                });
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
