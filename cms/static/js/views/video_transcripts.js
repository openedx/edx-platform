define(
    ['underscore', 'gettext', 'js/views/baseview', 'common/js/components/views/feedback_prompt',
        'edx-ui-toolkit/js/utils/html-utils', 'edx-ui-toolkit/js/utils/string-utils',
        'text!templates/video-transcripts.underscore', 'text!templates/video-transcript-upload-status.underscore'],
    function(_, gettext, BaseView, PromptView, HtmlUtils, StringUtils, videoTranscriptsTemplate,
                videoTranscriptUploadStatusTemplate) {
        'use strict';

        var VideoTranscriptsView = BaseView.extend({
            tagName: 'div',

            events: {
                'click .toggle-show-transcripts-button': 'toggleShowTranscripts',
                'click .upload-transcript-button': 'chooseFile',
                'click .more-details-action': 'showUploadFailureMessage'
            },

            initialize: function(options) {
                this.transcripts = options.transcripts;
                this.edxVideoID = options.edxVideoID;
                this.clientVideoID = options.clientVideoID;
                this.transcriptAvailableLanguages = options.transcriptAvailableLanguages;
                this.videoSupportedFileFormats = options.videoSupportedFileFormats;
                this.videoTranscriptSettings = options.videoTranscriptSettings;
                this.template = HtmlUtils.template(videoTranscriptsTemplate);
                this.transcriptUploadStatusTemplate = HtmlUtils.template(videoTranscriptUploadStatusTemplate);
                this.defaultFailureTitle = gettext('Your file could not be uploaded');
                this.defaultFailureMessage = gettext('This may be happening because of an error with our server or your internet connection. Try refreshing the page or making sure you are online.'); // eslint-disable-line max-len
                this.transcriptUploadStatuses = {
                    uploaded: {
                        statusClass: 'success',
                        iconClasses: 'fa-check',
                        shortMessage: 'Transcript uploaded.',
                        hiddenClass: 'hidden'
                    },
                    uploading: {
                        statusClass: '',
                        iconClasses: 'fa-spinner fa-pulse',
                        shortMessage: 'Uploading transcript',
                        hiddenClass: 'hidden'
                    },
                    failed: {
                        statusClass: 'error',
                        iconClasses: 'fa-warning',
                        shortMessage: 'Upload failed.',
                        hiddenClass: ''
                    },
                    validationFailed: {
                        statusClass: 'error',
                        iconClasses: 'fa-warning',
                        shortMessage: 'Validation failed.',
                        hiddenClass: ''
                    }
                };
                // This is needed to attach transcript methods to this object while uploading.
                _.bindAll(
                    this, 'render', 'chooseFile', 'transcriptSelected', 'transcriptUploadSucceeded',
                    'transcriptUploadFailed'
                );
            },

            /*
            Sorts object by value and returns a sorted array.
            */
            sortByValue: function(itemObject) {
                var sortedArray = [];
                _.each(itemObject, function(value, key) {
                    // Push each JSON Object entry in array by [value, key]
                    sortedArray.push([value, key]);
                });
                return sortedArray.sort();
            },

            /*
            Returns transcript title.
            */
            getTranscriptClientTitle: function() {
                var clientTitle = this.clientVideoID;
                // Remove video file extension for transcript title.
                _.each(this.videoSupportedFileFormats, function(videoFormat) {
                    clientTitle = clientTitle.replace(videoFormat, '');
                });
                return clientTitle.substring(0, 20);
            },

            /*
            Toggles Show/Hide transcript button and transcripts container.
            */
            toggleShowTranscripts: function() {
                var $transcriptsWrapperEl = this.$el.find('.show-video-transcripts-wrapper');

                // Toggle show transcript wrapper.
                $transcriptsWrapperEl.toggleClass('hidden');

                // Toggle button text.
                HtmlUtils.setHtml(
                    this.$el.find('.toggle-show-transcripts-button-text'),
                    StringUtils.interpolate(
                        gettext('{toggleShowTranscriptText} transcripts ({totalTranscripts})'),
                        {
                            toggleShowTranscriptText: $transcriptsWrapperEl.hasClass('hidden') ? gettext('Show') : gettext('Hide'), // eslint-disable-line max-len
                            totalTranscripts: _.size(this.transcripts)
                        }
                    )
                );

                // Toggle icon class.
                if ($transcriptsWrapperEl.hasClass('hidden')) {
                    this.$el.find('.toggle-show-transcripts-icon').removeClass('fa-caret-down').addClass('fa-caret-right'); // eslint-disable-line max-len
                } else {
                    this.$el.find('.toggle-show-transcripts-icon').removeClass('fa-caret-right').addClass('fa-caret-down'); // eslint-disable-line max-len
                }
            },

            validateTranscriptUpload: function(file) {
                var errorMessage = '',
                    fileName = file.name,
                    fileType = fileName.substr(fileName.lastIndexOf('.') + 1);

                if (fileType !== this.videoTranscriptSettings.trancript_download_file_format) {
                    errorMessage = gettext(
                        '{filename} is not in a supported file format. ' +
                        'Supported file format is {supportedFileFormat}.'
                    )
                    .replace('{filename}', fileName)
                    .replace('{supportedFileFormat}', this.videoTranscriptSettings.trancript_download_file_format);
                }

                return errorMessage;
            },

            chooseFile: function(event) {
                var $transcriptContainer = $(event.target).parents('.show-video-transcript-content'),
                    $transcriptUploadEl = $transcriptContainer.find('.upload-transcript-input');

                $transcriptUploadEl.fileupload({
                    url: this.videoTranscriptSettings.transcript_upload_handler_url,
                    add: this.transcriptSelected,
                    done: this.transcriptUploadSucceeded,
                    fail: this.transcriptUploadFailed,
                    formData: {
                        edx_video_id: this.edxVideoID,
                        language_code: $transcriptContainer.attr('data-language-code'),
                        new_language_code: $transcriptContainer.find('.transcript-language-menu').val()
                    }
                });

                $transcriptUploadEl.click();
            },

            transcriptSelected: function(event, data) {
                var errorMessage,
                    $transcriptContainer = $(event.target).parents('.show-video-transcript-content');

                errorMessage = this.validateTranscriptUpload(data.files[0]);
                if (!errorMessage) {
                    // Do not trigger global AJAX error handler
                    data.global = false;    // eslint-disable-line no-param-reassign
                    data.submit();
                    this.renderMessage($transcriptContainer, 'uploading');
                } else {
                    // Reset transcript language back to original.
                    $transcriptContainer.find('.transcript-language-menu').val($transcriptContainer.attr('data-language-code')); // eslint-disable-line max-len
                    this.renderMessage($transcriptContainer, 'validationFailed', errorMessage);
                }
            },

            transcriptUploadSucceeded: function(event, data) {
                var languageCode = data.formData.language_code,
                    newLanguageCode = data.formData.new_language_code,
                    $transcriptContainer = this.$el.find('.show-video-transcript-content[data-language-code="' + languageCode + '"]');  // eslint-disable-line max-len

                $transcriptContainer.attr('data-language-code', newLanguageCode);
                HtmlUtils.setHtml(
                    $transcriptContainer.find('.transcript-title'),
                    StringUtils.interpolate(gettext('{transcriptClientTitle}_{transcriptLanguageCode}.{fileExtension}'),
                        {
                            transcriptClientTitle: this.getTranscriptClientTitle(),
                            transcriptLanguageCode: newLanguageCode,
                            fileExtension: this.videoTranscriptSettings.trancript_download_file_format
                        }
                    )
                );

                this.renderMessage($transcriptContainer, 'uploaded');
            },

            transcriptUploadFailed: function(event, data) {
                var errorMessage,
                    languageCode = data.formData.language_code,
                    $transcriptContainer = this.$el.find('.show-video-transcript-content[data-language-code="' + languageCode + '"]');  // eslint-disable-line max-len

                try {
                    errorMessage = JSON.parse(data.jqXHR.responseText).error;
                    errorMessage = errorMessage || this.defaultFailureMessage;
                } catch (error) {
                    errorMessage = this.defaultFailureMessage;
                }
                // Reset transcript language back to original.
                $transcriptContainer.find('.transcript-language-menu').val(languageCode);

                this.renderMessage($transcriptContainer, 'failed', errorMessage);
            },

            clearMessage: function() {
                var $transcriptStatusesEl = this.$el.find('.transcript-upload-status-container');
                // Clear all message containers
                HtmlUtils.setHtml($transcriptStatusesEl, '');
                $transcriptStatusesEl.removeClass('success error');
            },

            renderMessage: function($transcriptContainer, status, errorMessage) {
                var statusData = this.transcriptUploadStatuses[status],
                    $transcriptStatusEl = $transcriptContainer.find('.transcript-upload-status-container');

                // If a messge is already present above the video transcript element, remove it.
                this.clearMessage();

                HtmlUtils.setHtml(
                    $transcriptStatusEl,
                    this.transcriptUploadStatusTemplate({
                        status: statusData.statusClass,
                        iconClasses: statusData.iconClasses,
                        shortMessage: gettext(statusData.shortMessage),
                        errorMessage: errorMessage || '',
                        hiddenClass: statusData.hiddenClass
                    })
                );

                $transcriptStatusEl.addClass(statusData.statusClass);
            },

            showUploadFailureMessage: function(event) {
                var errorMessage = $(event.target).data('error-message');
                return new PromptView.Warning({
                    title: this.defaultFailureTitle,
                    message: errorMessage,
                    actions: {
                        primary: {
                            text: gettext('Close'),
                            click: function(prompt) {
                                return prompt.hide();
                            }
                        }
                    }
                }).show();
            },

            /*
            Renders transcripts view.
            */
            render: function() {
                HtmlUtils.setHtml(
                    this.$el,
                    this.template({
                        transcripts: this.transcripts,
                        transcriptAvailableLanguages: this.sortByValue(this.transcriptAvailableLanguages),
                        edxVideoID: this.edxVideoID,
                        transcriptClientTitle: this.getTranscriptClientTitle(),
                        transcriptFileFormat: this.videoTranscriptSettings.trancript_download_file_format,
                        transcriptDownloadHandlerUrl: this.videoTranscriptSettings.transcript_download_handler_url
                    })
                );
                return this;
            }
        });

        return VideoTranscriptsView;
    }
);
