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
             * The allowed file extensions of the uploaded file, as a comma-separated string (ex, ".csv,.txt").
             * Some browsers will enforce that only files with these extensions can be uploaded,
             * but others (for instance, Firefox), will not. By default, no extensions are specified and any
             * file can be uploaded.
             */
            extensions: '',
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
