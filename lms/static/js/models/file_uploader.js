(function(Backbone) {
    var FileUploaderModel = Backbone.Model.extend({
        defaults: {
            /**
             * The title to display.
             */
            title: '',
            /**
             * The description of what can be uploaded.
             */
            description: '',
            /**
             * The expected file extension of the uploaded file. Some browsers will enforce
             * that the uploaded file has this extension, but others (for instance, Firefox),
             * will not.
             */
            extension: '',
            /**
             * The url for posting the uploaded file.
             */
            url: ''
        }
    });

    this.FileUploaderModel = FileUploaderModel;
}).call(this, Backbone);
