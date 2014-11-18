define(
    ["jquery", "underscore", "js/models/active_video_upload", "js/views/baseview", "js/views/active_video_upload", "jquery.fileupload"],
    function($, _, ActiveVideoUpload, BaseView, ActiveVideoUploadView) {
        "use strict";

        var ActiveVideoUploadListView = BaseView.extend({
            tagName: "div",
            events: {
                "click .js-upload-button": "chooseFile"
            },

            initialize: function() {
                this.template = this.loadTemplate("active-video-upload-list");
            },

            render: function() {
                this.$el.html(this.template());
                this.uploadForm = this.$(".form-file-drop");
                this.uploadForm.fileupload({
                    type: "PUT",
                    autoUpload: true,
                    singleFileUploads: false,
                    add: this.fileUploadAdd.bind(this),
                    send: this.fileUploadSend,
                    done: this.fileUploadDone,
                    fail: this.fileUploadFail
                });
                return this;
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
                    uploadData.model = model;
                    uploadData.submit();
                    var itemView = new ActiveVideoUploadView({model: model});
                    view.$(".js-active-video-upload-list").append(itemView.render().$el);
                } else {
                    $.ajax({
                        contentType: "application/json",
                        data: JSON.stringify({
                            files: _.map(
                                uploadData.files,
                                function(file) { return {"file-name": file.name}; }
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
                                    global: false,  // Do not trigger global AJAX error handler
                                    redirected: true
                                });
                            }
                        );
                    });
                }
            },

            fileUploadSend: function(event, data) {
                data.model.uploadStarted();
            },

            fileUploadDone: function(event, data) {
                data.model.uploadCompleted();
            },

            fileUploadFail: function(event, data) {
                data.model.uploadFailed();
            }
        });

        return ActiveVideoUploadListView;
    }
);
