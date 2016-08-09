/**
 * A view for uploading a file.
 *
 * Currently only single-file upload is supported (to support multiple-file uploads, the HTML
 * input must be changed to specify "multiple" and the notification messaging needs to be changed
 * to support the display of multiple status messages).
 *
 * There is no associated model, but the view supports the following options:
 *
 * @param title, the title to display.
 * @param inputLabel, a label that will be added for the file input field. Note that this label is only shown to
 *     screen readers.
 * @param inputTip, a tooltip linked to the file input field. Can be used to state what sort of file can be uploaded.
 * @param extensions, the allowed file extensions of the uploaded file, as a comma-separated string (ex, ".csv,.txt").
 *     Some browsers will enforce that only files with these extensions can be uploaded, but others
 *     (for instance, Firefox), will not. By default, no extensions are specified and any file can be uploaded.
 * @param submitButtonText, text to display on the submit button to upload the file. The default value for this is
 *     "Upload File".
 * @param url, the url for posting the uploaded file.
 * @param successNotification, optional callback that can return a success NotificationModel for display
 *     after a file was successfully uploaded. This method will be passed the uploaded file, event, and data.
 * @param errorNotification, optional callback that can return a success NotificationModel for display
 *     after a file failed to upload. This method will be passed the attempted file, event, and data.
 */
(function(Backbone, $, _, gettext, interpolate_text, NotificationModel, NotificationView) {
    // Requires JQuery-File-Upload.
    var FileUploaderView = Backbone.View.extend({

        initialize: function(options) {
            this.template = _.template($('#file-upload-tpl').text());
            this.options = options;
        },

        render: function() {
            var options = this.options,
                get_option_with_default = function(option, default_value) {
                    var optionVal = options[option];
                    return optionVal ? optionVal : default_value;
                },
                submitButton, resultNotification;

            this.$el.html(this.template({
                title: get_option_with_default('title', ''),
                inputLabel: get_option_with_default('inputLabel', ''),
                inputTip: get_option_with_default('inputTip', ''),
                extensions: get_option_with_default('extensions', ''),
                submitButtonText: get_option_with_default('submitButtonText', gettext('Upload File')),
                url: get_option_with_default('url', '')
            }));

            submitButton = this.$el.find('.submit-file-button');
            resultNotification = this.$el.find('.result'),

            this.$el.find('#file-upload-form').fileupload({
                dataType: 'json',
                type: 'POST',
                done: this.successHandler.bind(this),
                fail: this.errorHandler.bind(this),
                autoUpload: false,
                replaceFileInput: false,
                add: function(e, data) {
                    var file = data.files[0];
                    submitButton.removeClass('is-disabled').attr('aria-disabled', false);
                    submitButton.unbind('click');
                    submitButton.click(function(event) {
                        event.preventDefault();
                        data.submit();
                    });
                    resultNotification.html('');
                }
            });

            return this;
        },

        successHandler: function(event, data) {
            var file = data.files[0].name;
            var notificationModel;
            if (this.options.successNotification) {
                notificationModel = this.options.successNotification(file, event, data);
            }
            else {
                notificationModel = new NotificationModel({
                    type: 'confirmation',
                    title: interpolate_text(gettext("Your upload of '{file}' succeeded."), {file: file})
                });
            }
            var notification = new NotificationView({
                el: this.$('.result'),
                model: notificationModel
            });
            notification.render();
        },

        errorHandler: function(event, data) {
            var file = data.files[0].name, message = null, jqXHR = data.response().jqXHR;
            var notificationModel;
            if (this.options.errorNotification) {
                notificationModel = this.options.errorNotification(file, event, data);
            }
            else {
                if (jqXHR.responseText) {
                    try {
                        message = JSON.parse(jqXHR.responseText).error;
                    }
                    catch (err) {
                    }
                }
                if (!message) {
                    message = interpolate_text(gettext("Your upload of '{file}' failed."), {file: file});
                }
                notificationModel = new NotificationModel({
                    type: 'error',
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
