/**
 * A view for uploading a file.
 *
 * Currently only single-file upload is supported (to support multiple-file uploads, the HTML
 * input must be changed to specify "multiple" and the notification messaging needs to be changed
 * to support the display of multiple status messages).
 *
 * The associated model is FileUploaderModel.
 */
(function(Backbone, $, _, gettext, interpolate_text, NotificationModel, NotificationView) {
    // Requires JQuery-File-Upload.
    var FileUploaderView = Backbone.View.extend({

        initialize: function(options) {
            this.template = _.template($('#file-upload-tpl').text());
            this.options = options;
        },

        render: function() {
            this.$el.html(this.template({
                model: this.model
            }));
            var submitButton= this.$el.find('.submit-file-button');
            var resultNotification = this.$el.find('.result');
            this.$el.find('#file-upload-form').fileupload({
                dataType: 'json',
                type: 'POST',
                done: this.successHandler.bind(this),
                fail: this.errorHandler.bind(this),
                autoUpload: false,
                replaceFileInput: false,
                add: function(e, data) {
                    var file = data.files[0];
                    submitButton.unbind('click');
                    submitButton.click(function(event){
                        event.preventDefault();
                        data.submit();
                    });
                    resultNotification.html("");
                 }
            });
            return this;
        },

        successHandler: function (event, data) {
            var file = data.files[0].name;
            var notificationModel;
            if (this.options.successNotification) {
                notificationModel = this.options.successNotification(file, event, data);
            }
            else {
                notificationModel = new NotificationModel({
                    type: "confirmation",
                    title: interpolate_text(gettext("Your upload of '{file}' succeeded."), {file: file})
                });
            }
            var notification = new NotificationView({
                el: this.$('.result'),
                model: notificationModel
            });
            notification.render();
        },

        errorHandler: function (event, data) {
            var file = data.files[0].name;
            var notificationModel;
            if (this.options.errorNotification) {
                notificationModel = this.options.errorNotification(file, event, data);
            }
            else {
                var message = null;
                var jqXHR = data.response().jqXHR;
                if (jqXHR.responseText) {
                    try {
                        message = JSON.parse(jqXHR.responseText).error;
                    }
                    catch(err) {
                    }
                }
                if (!message) {
                    message = interpolate_text(gettext("Your upload of '{file}' failed."), {file: file});
                }
                notificationModel = new NotificationModel({
                    type: "error",
                    title: message
                });
            }
            var notification = new NotificationView({
                el: this.$('.result'),
                model: notificationModel
            });
            notification.render();
        }
    });

    this.FileUploaderView = FileUploaderView;
}).call(this, Backbone, $, _, gettext, interpolate_text, NotificationModel, NotificationView);
