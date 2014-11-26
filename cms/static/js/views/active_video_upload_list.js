define(
    ["jquery", "underscore", "backbone", "js/models/active_video_upload", "js/views/baseview", "js/views/active_video_upload", "jquery.fileupload"],
    function($, _, Backbone, ActiveVideoUpload, BaseView, ActiveVideoUploadView) {
        "use strict";

        var ActiveVideoUploadListView = BaseView.extend({
            tagName: "div",
            events: {
                "click .js-upload-button": "chooseFile"
            },

            initialize: function(options) {
                this.template = this.loadTemplate("active-video-upload-list");
                this.collection = new Backbone.Collection();
                this.listenTo(this.collection, "add", this.renderUpload);
                this.concurrentUploadLimit = options.concurrentUploadLimit || 0;
                this.postUrl = options.postUrl;
                if (options.uploadButton) {
                    options.uploadButton.click(this.chooseFile.bind(this));
                }
            },

            render: function() {
                this.$el.html(this.template());
                this.uploadForm = this.$(".form-file-drop");
                this.uploadForm.fileupload({
                    type: "PUT",
                    autoUpload: true,
                    singleFileUploads: false,
                    limitConcurrentUploads: this.concurrentUploadLimit,
                    add: this.fileUploadAdd.bind(this),
                    send: this.fileUploadSend.bind(this),
                    done: this.fileUploadDone.bind(this),
                    fail: this.fileUploadFail.bind(this)
                });
                return this;
            },

            renderUpload: function(model) {
                var itemView = new ActiveVideoUploadView({model: model});
                this.$(".js-active-video-upload-list").append(itemView.render().$el);
            },

            chooseFile: function(event) {
                event.preventDefault();
                this.uploadForm.find(".js-file-input").click();
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
                        url: view.postUrl,
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
                                view.uploadForm.fileupload("add", {
                                    files: [uploadData.files[index]],
                                    url: file["upload-url"],
                                    multipart: false,
                                    global: false,  // Do not trigger global AJAX error handler
                                    redirected: true
                                });
                            }
                        );
                    });
                }
            },

            fileUploadSend: function(event, data) {
                this.collection.get(data.cid).set("status", ActiveVideoUpload.STATUS_UPLOADING);
            },

            fileUploadDone: function(event, data) {
                this.collection.get(data.cid).set("status", ActiveVideoUpload.STATUS_COMPLETED);
            },

            fileUploadFail: function(event, data) {
                this.collection.get(data.cid).set("status", ActiveVideoUpload.STATUS_FAILED);
            }
        });

        return ActiveVideoUploadListView;
    }
);
