(function(Backbone, gettext) {
    var FileUploaderModel = Backbone.Model.extend({
        defaults: {
            /**
             * The title to display.
             */
            title: '',
            /**
             * A label that will be added for the file input field.
             */
            inputLabel: '',
            /**
             * A tooltip linked to the file input field. Can be used to state what sort of file
             * can be uploaded.
             */
            inputTip: '',
            /**
             * The expected file extension of the uploaded file. Some browsers will enforce
             * that the uploaded file has this extension, but others (for instance, Firefox),
             * will not.
             */
            extension: '',
            /**
             * Text to display on the submit button to upload the file. The default value for this is
             * "Upload File".
             */
            submitButtonText: gettext("Upload File"),
            /**
             * The url for posting the uploaded file.
             */
            url: ''
        }
    });

    this.FileUploaderModel = FileUploaderModel;
}).call(this, Backbone, gettext);
