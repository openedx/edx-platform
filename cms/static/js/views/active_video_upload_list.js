define([
    'jquery',
    'underscore',
    'underscore.string',
    'backbone',
    'js/models/active_video_upload',
    'js/views/baseview',
    'js/views/active_video_upload',
    'common/js/components/views/feedback_notification',
    'edx-ui-toolkit/js/utils/html-utils',
    'text!templates/active-video-upload-list.underscore',
    'jquery.fileupload'
],
    function($, _, str, Backbone, ActiveVideoUpload, BaseView, ActiveVideoUploadView, NotificationView, HtmlUtils,
             activeVideoUploadListTemplate) {
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

            initialize: function(options) {
                this.template = HtmlUtils.template(activeVideoUploadListTemplate)({});
                this.collection = new Backbone.Collection();
                this.itemViews = [];
                this.listenTo(this.collection, 'add', this.addUpload);
                this.concurrentUploadLimit = options.concurrentUploadLimit || 0;
                this.postUrl = options.postUrl;
                this.videoSupportedFileFormats = options.videoSupportedFileFormats;
                this.videoUploadMaxFileSizeInGB = options.videoUploadMaxFileSizeInGB;
                this.onFileUploadDone = options.onFileUploadDone;
                if (options.uploadButton) {
                    options.uploadButton.click(this.chooseFile.bind(this));
                }
                // error message modal for file uploads
                this.fileErrorMsg = null;
            },

            render: function() {
                HtmlUtils.setHtml(
                    this.$el,
                    this.template
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
                var preventDefault = function(event) {
                    event.preventDefault();
                };
                $(window).on('dragover', preventDefault);
                $(window).on('drop', preventDefault);
                $(window).on('beforeunload', this.onBeforeUnload.bind(this));

                return this;
            },

            onBeforeUnload: function() {
                // Are there are uploads queued or in progress?
                var uploading = this.collection.filter(function(model) {
                    var stat = model.get('status');
                    return (model.get('progress') < 1) &&
                          ((stat === ActiveVideoUpload.STATUS_QUEUED ||
                           (stat === ActiveVideoUpload.STATUS_UPLOADING)));
                });
                // If so, show a warning message.
                if (uploading.length) {
                    return gettext('Your video uploads are not complete.');
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
                // hide error message if any present.
                this.hideErrorMessage();
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
                    errorMsg;

                // Validate file
                errorMsg = view.validateFile(uploadData);
                if (errorMsg) {
                    view.showErrorMessage(errorMsg);
                } else {
                    if (uploadData.redirected) {
                        model = new ActiveVideoUpload({
                            fileName: uploadData.files[0].name,
                            videoId: uploadData.videoId
                        });
                        this.collection.add(model);
                        uploadData.cid = model.cid; // eslint-disable-line no-param-reassign
                        uploadData.submit();
                    } else {
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
                                    if (response.responseText) {
                                        try {
                                            errorMsg = JSON.parse(response.responseText).error;
                                        } catch (error) {
                                            errorMsg = str.truncate(response.responseText, 300);
                                        }
                                    } else {
                                        errorMsg = gettext('This may be happening because of an error with our server or your internet connection. Try refreshing the page or making sure you are online.');  // eslint-disable-line max-len
                                    }
                                    view.showErrorMessage(errorMsg);
                                });
                            }
                        );
                    }
                }
            },

            setStatus: function(cid, status) {
                this.collection.get(cid).set('status', status);
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
                this.setStatus(data.cid, ActiveVideoUpload.STATUS_COMPLETED);
                this.setProgress(data.cid, 1);
                if (this.onFileUploadDone) {
                    this.onFileUploadDone(this.collection);
                    this.clearSuccessful();
                }
            },

            fileUploadFail: function(event, data) {
                this.setStatus(data.cid, ActiveVideoUpload.STATUS_FAILED);
            },

            getMaxFileSizeInBytes: function() {
                return this.videoUploadMaxFileSizeInGB * CONVERSION_FACTOR_GBS_TO_BYTES;
            },

            hideErrorMessage: function() {
                if (this.fileErrorMsg) {
                    this.fileErrorMsg.hide();
                    this.fileErrorMsg = null;
                }
            },

            readMessages: function(messages) {
                if ($(window).prop('SR') !== undefined) {
                    $(window).prop('SR').readTexts(messages);
                }
            },

            showErrorMessage: function(errorMsg) {
                var titleMsg;
                if (!this.fileErrorMsg) {
                    titleMsg = gettext('Your file could not be uploaded');
                    this.fileErrorMsg = new NotificationView.Error({
                        title: titleMsg,
                        message: errorMsg
                    });
                    this.fileErrorMsg.show();
                    this.readMessages([titleMsg, errorMsg]);
                }
            },

            validateFile: function(data) {
                var self = this,
                    error = '',
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
                        return false;
                    }
                    if (file.size > self.getMaxFileSizeInBytes()) {
                        error = gettext(
                            '{filename} exceeds maximum size of {maxFileSizeInGB} GB.'
                        )
                        .replace('{filename}', fileName)
                        .replace('{maxFileSizeInGB}', self.videoUploadMaxFileSizeInGB);
                        return false;
                    }
                });
                return error;
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
            }
        });

        return ActiveVideoUploadListView;
    }
);
