define(
    ["jquery", "underscore", "backbone", "js/models/active_video_upload", "js/views/baseview", "js/views/active_video_upload", "jquery.fileupload"],
    function($, _, Backbone, ActiveVideoUpload, BaseView, ActiveVideoUploadView) {
        "use strict";

        var ActiveVideoUploadListView = BaseView.extend({
            tagName: "div",
            events: {
                "click .file-drop-area": "chooseFile",
                "dragleave .file-drop-area": "dragleave",
                "drop .file-drop-area": "dragleave"
            },

            initialize: function(options) {
                this.template = this.loadTemplate("active-video-upload-list");
                this.collection = new Backbone.Collection();
                this.itemViews = [];
                this.listenTo(this.collection, "add", this.addUpload);
                this.concurrentUploadLimit = options.concurrentUploadLimit || 0;
                this.postUrl = options.postUrl;
                if (options.uploadButton) {
                    options.uploadButton.click(this.chooseFile.bind(this));
                }
            },

            render: function() {
                this.$el.html(this.template());
                _.each(this.itemViews, this.renderUploadView.bind(this));
                this.$uploadForm = this.$(".file-upload-form");
                this.$dropZone = this.$uploadForm.find(".file-drop-area");
                this.$uploadForm.fileupload({
                    type: "PUT",
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
                $(window).on("dragover", preventDefault);
                $(window).on("drop", preventDefault);
                $(window).on("beforeunload", this.onBeforeUnload.bind(this));

                return this;
            },

            onBeforeUnload: function () {
                // Are there are uploads queued or in progress?
                var uploading = this.collection.filter(function(model) {
                    var stat = model.get("status");
                    return (model.get("progress") < 1) &&
                          ((stat === ActiveVideoUpload.STATUS_QUEUED ||
                           (stat === ActiveVideoUpload.STATUS_UPLOADING)));
                });
                // If so, show a warning message.
                if (uploading.length) {
                    return gettext("Your video uploads are not complete.");
                }
            },

            addUpload: function(model) {
                var itemView = new ActiveVideoUploadView({model: model});
                this.itemViews.push(itemView);
                this.renderUploadView(itemView);
            },

            renderUploadView: function(view) {
                this.$(".active-video-upload-list").append(view.render().$el);
            },

            chooseFile: function(event) {
                event.preventDefault();
                this.$uploadForm.find(".js-file-input").click();
            },

            dragover: function(event) {
                event.preventDefault();
                this.$dropZone.addClass("is-dragged");
            },

            dragleave: function(event) {
                event.preventDefault();
                this.$dropZone.removeClass("is-dragged");
            },

            // Each file is ultimately sent to a separate URL, but we want to make a
            // single API call to get the URLs for all videos that the user wants to
            // upload at one time. The file upload plugin only allows for this one
            // callback, so this makes the API call and then breaks apart the
            // individual file uploads, using the extra `redirected` field to
            // indicate that the correct upload url has already been retrieved
            fileUploadAdd: function(event, uploadData) {
                var view = this;
                if (uploadData.redirected) {
                    var model = new ActiveVideoUpload({fileName: uploadData.files[0].name});
                    this.collection.add(model);
                    uploadData.cid = model.cid;
                    uploadData.submit();
                } else {
                    $.ajax({
                        url: this.postUrl,
                        contentType: "application/json",
                        data: JSON.stringify({
                            files: _.map(
                                uploadData.files,
                                function(file) {
                                    return {"file_name": file.name, "content_type": file.type};
                                }
                            )
                        }),
                        dataType: "json",
                        type: "POST"
                    }).done(function(responseData) {
                        _.each(
                            responseData["files"],
                            function(file, index) {
                                view.$uploadForm.fileupload("add", {
                                    files: [uploadData.files[index]],
                                    url: file["upload_url"],
                                    multipart: false,
                                    global: false,  // Do not trigger global AJAX error handler
                                    redirected: true
                                });
                            }
                        );
                    });
                }
            },

            setStatus: function(cid, status) {
                this.collection.get(cid).set("status", status);
            },

            // progress should be a number between 0 and 1 (inclusive)
            setProgress: function(cid, progress) {
                this.collection.get(cid).set("progress", progress);
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
            },

            fileUploadFail: function(event, data) {
                this.setStatus(data.cid, ActiveVideoUpload.STATUS_FAILED);
            }
        });

        return ActiveVideoUploadListView;
    }
);
