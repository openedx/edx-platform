define([
    'jquery',
    'underscore',
    'backbone',
    'js/models/active_video_upload',
    'js/views/baseview',
    'js/views/active_video_upload',
    'js/views/course_video_settings',
    'edx-ui-toolkit/js/utils/html-utils',
    'edx-ui-toolkit/js/utils/string-utils',
    'text!templates/active-video-upload-list.underscore',
    'jquery.fileupload'
],
function($, _, Backbone, ActiveVideoUpload, BaseView, ActiveVideoUploadView, CourseVideoSettingsView,
    HtmlUtils, StringUtils, activeVideoUploadListTemplate) {
    'use strict';
    var ActiveVideoUploadListView,
        CONVERSION_FACTOR_GBS_TO_BYTES = 1000 * 1000 * 1000;
    ActiveVideoUploadListView = BaseView.extend({
        tagName: 'div',
        events: {
            'click .file-drop-area': 'chooseFile',
            'dragleave .file-drop-area': 'dragleave',
            'drop .file-drop-area': 'dragleave'
        },

        uploadHeader: gettext('Upload Videos'),
        uploadText: HtmlUtils.interpolateHtml(
            gettext('Drag and drop or {spanStart}browse your computer{spanEnd}.'),
            {
                spanStart: HtmlUtils.HTML('<span class="upload-text-link">'),
                spanEnd: HtmlUtils.HTML('</span>')
            }
        ),
        defaultFailureMessage: gettext('This may be happening because of an error with our server or your internet connection. Try refreshing the page or making sure you are online.'),  // eslint-disable-line max-len

        initialize: function(options) {
            this.template = HtmlUtils.template(activeVideoUploadListTemplate);
            this.collection = new Backbone.Collection();
            this.itemViews = [];
            this.listenTo(this.collection, 'add', this.addUpload);
            this.concurrentUploadLimit = options.concurrentUploadLimit || 0;
            this.postUrl = options.postUrl;
            this.activeTranscriptPreferences = options.activeTranscriptPreferences;
            this.transcriptOrganizationCredentials = options.transcriptOrganizationCredentials;
            this.videoTranscriptSettings = options.videoTranscriptSettings;
            this.isVideoTranscriptEnabled = options.isVideoTranscriptEnabled;
            this.videoSupportedFileFormats = options.videoSupportedFileFormats;
            this.videoUploadMaxFileSizeInGB = options.videoUploadMaxFileSizeInGB;
            this.onFileUploadDone = options.onFileUploadDone;
            if (options.courseVideoSettingsButton) {
                options.courseVideoSettingsButton.click(this.showCourseVideoSettingsView.bind(this));
            }

            this.maxSizeText = StringUtils.interpolate(
                gettext('Maximum file size: {maxFileSize} GB'),
                {
                    maxFileSize: this.videoUploadMaxFileSizeInGB
                }
            );
            this.supportedVideosText = edx.StringUtils.interpolate(
                gettext('Supported file types: {supportedVideoTypes}'),
                {
                    supportedVideoTypes: this.videoSupportedFileFormats.join(', ')
                }
            );
            if (this.isVideoTranscriptEnabled) {
                this.listenTo(
                    Backbone,
                    'coursevideosettings:syncActiveTranscriptPreferences',
                    this.syncActiveTranscriptPreferences
                );
                this.listenTo(
                    Backbone,
                    'coursevideosettings:destroyCourseVideoSettingsView',
                    this.destroyCourseVideoSettingsView
                );
            }
        },

        syncActiveTranscriptPreferences: function(activeTranscriptPreferences) {
            this.activeTranscriptPreferences = activeTranscriptPreferences;
        },

        showCourseVideoSettingsView: function(event) {
            if (this.isVideoTranscriptEnabled) {
                this.courseVideoSettingsView = new CourseVideoSettingsView({
                    activeTranscriptPreferences: this.activeTranscriptPreferences,
                    transcriptOrganizationCredentials: this.transcriptOrganizationCredentials,
                    videoTranscriptSettings: this.videoTranscriptSettings
                });
                this.courseVideoSettingsView.render();
                event.stopPropagation();
            }
        },

        destroyCourseVideoSettingsView: function() {
            this.courseVideoSettingsView = null;
        },

        render: function() {
            var preventDefault;

            HtmlUtils.setHtml(
                this.$el,
                this.template({
                    uploadHeader: this.uploadHeader,
                    uploadText: this.uploadText,
                    maxSizeText: this.maxSizeText,
                    supportedVideosText: this.supportedVideosText
                })
            );
            _.each(this.itemViews, this.renderUploadView.bind(this));
            this.$uploadForm = this.$('.file-upload-form');
            this.$dropZone = this.$uploadForm.find('.file-drop-area');
            this.$uploadForm.fileupload({
                type: 'PUT',
                singleFileUploads: false,
                limitConcurrentUploads: this.concurrentUploadLimit,
                dropZone: this.$dropZone,
                dragover: this.dragover.bind(this),
                add: this.fileUploadAdd.bind(this),
                send: this.fileUploadSend.bind(this),
                progress: this.fileUploadProgress.bind(this),
                done: this.fileUploadDone.bind(this),
                fail: this.fileUploadFail.bind(this)
            });

            // Disable default drag and drop behavior for the window (which
            // is to load the file in place)
            preventDefault = function(event) {
                event.preventDefault();
            };
            $(window).on('dragover', preventDefault);
            $(window).on('drop', preventDefault);
            $(window).on('beforeunload', this.onBeforeUnload.bind(this));
            $(window).on('unload', this.onUnload.bind(this));
            return this;
        },

        onBeforeUnload: function() {
            // Are there are uploads queued or in progress?
            var uploading = this.collection.filter(function(model) {
                var isUploading = model.uploading();
                if (isUploading) {
                    model.set('uploading', true);
                } else {
                    model.set('uploading', false);
                }
                return isUploading;
            });

            // If so, show a warning message.
            if (uploading.length) {
                return gettext('Your video uploads are not complete.');
            }
        },

        onUnload: function() {
            var statusUpdates = [];
            this.collection.each(function(model) {
                if (model.get('uploading')) {
                    statusUpdates.push(
                        {
                            edxVideoId: model.get('videoId'),
                            status: 'upload_cancelled',
                            message: 'User cancelled video upload'
                        }
                    );
                }
            });

            if (statusUpdates.length > 0) {
                this.sendStatusUpdate(statusUpdates);
            }
        },

        addUpload: function(model) {
            var itemView = new ActiveVideoUploadView({model: model});
            this.itemViews.push(itemView);
            this.renderUploadView(itemView);
        },

        renderUploadView: function(view) {
            this.$('.active-video-upload-list').append(view.render().$el);
        },

        chooseFile: function(event) {
            event.preventDefault();
            this.$uploadForm.find('.js-file-input').click();
        },

        dragover: function(event) {
            event.preventDefault();
            this.$dropZone.addClass('is-dragged');
        },

        dragleave: function(event) {
            event.preventDefault();
            this.$dropZone.removeClass('is-dragged');
        },

        // Each file is ultimately sent to a separate URL, but we want to make a
        // single API call to get the URLs for all videos that the user wants to
        // upload at one time. The file upload plugin only allows for this one
        // callback, so this makes the API call and then breaks apart the
        // individual file uploads, using the extra `redirected` field to
        // indicate that the correct upload url has already been retrieved
        fileUploadAdd: function(event, uploadData) {
            var view = this,
                model,
                errors,
                errorMsg;

            if (uploadData.redirected) {
                model = new ActiveVideoUpload({
                    fileName: uploadData.files[0].name,
                    videoId: uploadData.videoId
                });
                this.collection.add(model);
                uploadData.cid = model.cid; // eslint-disable-line no-param-reassign
                uploadData.submit();
            } else {
                // Validate file and remove the files with errors
                errors = view.validateFile(uploadData);
                _.each(errors, function(error) {
                    view.addUploadFailureView(error.fileName, error.message);
                    uploadData.files.splice(
                        _.findIndex(uploadData.files, function(file) { return file.name === error.fileName; }), 1
                    );
                });
                _.each(
                    uploadData.files,
                    function(file) {
                        $.ajax({
                            url: view.postUrl,
                            contentType: 'application/json',
                            data: JSON.stringify({
                                files: [{file_name: file.name, content_type: file.type}]
                            }),
                            dataType: 'json',
                            type: 'POST',
                            global: false   // Do not trigger global AJAX error handler
                        }).done(function(responseData) {
                            _.each(
                                responseData.files,
                                function(file) { // eslint-disable-line no-shadow
                                    view.$uploadForm.fileupload('add', {
                                        files: _.filter(uploadData.files, function(fileObj) {
                                            return file.file_name === fileObj.name;
                                        }),
                                        url: file.upload_url,
                                        videoId: file.edx_video_id,
                                        multipart: false,
                                        global: false,  // Do not trigger global AJAX error handler
                                        redirected: true
                                    });
                                }
                            );
                        }).fail(function(response) {
                            try {
                                errorMsg = JSON.parse(response.responseText).error;
                            } catch (error) {
                                errorMsg = view.defaultFailureMessage;
                            }
                            view.addUploadFailureView(file.name, errorMsg);
                        });
                    }
                );
            }
        },

        setStatus: function(cid, status, failureMessage) {
            this.collection.get(cid).set({status: status, failureMessage: failureMessage || null});
        },

        // progress should be a number between 0 and 1 (inclusive)
        setProgress: function(cid, progress) {
            this.collection.get(cid).set('progress', progress);
        },

        fileUploadSend: function(event, data) {
            this.setStatus(data.cid, ActiveVideoUpload.STATUS_UPLOADING);
        },

        fileUploadProgress: function(event, data) {
            this.setProgress(data.cid, data.loaded / data.total);
        },

        fileUploadDone: function(event, data) {
            var model = this.collection.get(data.cid),
                self = this;

            this.readMessages([
                StringUtils.interpolate(
                    gettext('Upload completed for video {fileName}'),
                    {fileName: model.get('fileName')}
                )
            ]);

            this.sendStatusUpdate([
                {
                    edxVideoId: model.get('videoId'),
                    status: 'upload_completed',
                    message: 'Uploaded completed'
                }
            ]).done(function() {
                self.setStatus(data.cid, ActiveVideoUpload.STATUS_COMPLETED);
                self.setProgress(data.cid, 1);
                if (self.onFileUploadDone) {
                    self.onFileUploadDone(self.collection);
                    self.clearSuccessful();
                }
            });
        },

        fileUploadFail: function(event, data) {
            var responseText = data.jqXHR.responseText,
                message = this.defaultFailureMessage,
                status = 'upload_failed',
                model = this.collection.get(data.cid);

            if (responseText && data.jqXHR.getResponseHeader('content-type') === 'application/xml') {
                message = $(responseText).find('Message').text();
                status = 's3_upload_failed';
            }

            this.readMessages([
                StringUtils.interpolate(
                    gettext('Upload failed for video {fileName}'),
                    {fileName: model.get('fileName')}
                )
            ]);

            this.sendStatusUpdate([
                {
                    edxVideoId: model.get('videoId'),
                    status: status,
                    message: message
                }
            ]);
            this.setStatus(data.cid, ActiveVideoUpload.STATUS_FAILED, message);
        },

        addUploadFailureView: function(fileName, failureMessage) {
            var model = new ActiveVideoUpload({
                fileName: fileName,
                status: ActiveVideoUpload.STATUS_FAILED,
                failureMessage: failureMessage
            });
            this.collection.add(model);
            this.readMessages([
                StringUtils.interpolate(
                    gettext('Upload failed for video {fileName}'),
                    {fileName: model.get('fileName')}
                )
            ]);
        },

        getMaxFileSizeInBytes: function() {
            return this.videoUploadMaxFileSizeInGB * CONVERSION_FACTOR_GBS_TO_BYTES;
        },

        readMessages: function(messages) {
            if ($(window).prop('SR') !== undefined) {
                $(window).prop('SR').readTexts(messages);
            }
        },

        validateFile: function(data) {
            var self = this,
                error = null,
                errors = [],
                fileName,
                fileType;

            $.each(data.files, function(index, file) {  // eslint-disable-line consistent-return
                fileName = file.name;
                fileType = fileName.substr(fileName.lastIndexOf('.'));
                // validate file type
                if (!_.contains(self.videoSupportedFileFormats, fileType)) {
                    error = gettext(
                        '{filename} is not in a supported file format. ' +
                            'Supported file formats are {supportedFileFormats}.'
                    )
                        .replace('{filename}', fileName)
                        .replace('{supportedFileFormats}', self.videoSupportedFileFormats.join(' and '));
                } else if (file.size > self.getMaxFileSizeInBytes()) {
                    error = gettext(
                        '{filename} exceeds maximum size of {maxFileSizeInGB} GB.'
                    )
                        .replace('{filename}', fileName)
                        .replace('{maxFileSizeInGB}', self.videoUploadMaxFileSizeInGB);
                }

                if (error) {
                    errors.push({
                        fileName: fileName,
                        message: error
                    });
                    error = null;
                }
            });
            return errors;
        },

        removeViewAt: function(index) {
            this.itemViews.splice(index);
            this.$('.active-video-upload-list li').eq(index).remove();
        },

        // Removes the upload progress view for files that have been
        // uploaded successfully. Also removes the corresponding models
        // from `collection`, keeping both in sync.
        clearSuccessful: function() {
            var idx,
                completedIndexes = [],
                completedModels = [],
                completedMessages = [];
            this.collection.each(function(model, index) {
                if (model.get('status') === ActiveVideoUpload.STATUS_COMPLETED) {
                    completedModels.push(model);
                    completedIndexes.push(index - completedIndexes.length);
                    completedMessages.push(model.get('fileName') +
                            gettext(': video upload complete.'));
                }
            });
            for (idx = 0; idx < completedIndexes.length; idx++) {
                this.removeViewAt(completedIndexes[idx]);
                this.collection.remove(completedModels[idx]);
            }
            // Alert screen readers that the uploads were successful
            if (completedMessages.length) {
                completedMessages.push(gettext('Previous Uploads table has been updated.'));
                this.readMessages(completedMessages);
            }
        },

        sendStatusUpdate: function(statusUpdates) {
            return $.ajax({
                url: this.postUrl,
                contentType: 'application/json',
                data: JSON.stringify(statusUpdates),
                dataType: 'json',
                type: 'POST'
            });
        }
    });

    return ActiveVideoUploadListView;
}
);
