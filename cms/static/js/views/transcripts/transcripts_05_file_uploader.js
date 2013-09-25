(function (window, undefined) {
    Transcripts.FileUploader = Backbone.View.extend({
        invisibleClass: 'is-invisible',

        // Pre-defined list of supported file formats.
        validFileExtensions: ['srt'],

        events: {
            'change .file-input': 'changeHadler',
            'click .setting-upload': 'clickHandler'
        },

        uploadTpl: '#transcripts-file-upload',

        initialize: function () {
            _.bindAll(this);

            this.file = false;
            this.render();
        },

        render: function () {
            var tpl = $(this.uploadTpl).text(),
                tplContainer = this.$el.find('.transcripts-file-uploader');

            if (tplContainer.length) {
                if (!tpl) {
                    console.error('Couldn\'t load Transcripts File Upload template');

                    return;
                }
                this.template = _.template(tpl);

                tplContainer.html(this.template({
                    ext: this.validFileExtensions,
                    component_id: this.options.component_id
                }));

                this.$form = this.$el.find('.file-chooser');
                this.$input = this.$form.find('.file-input');
                this.$progress = this.$el.find('.progress-fill');
            }
        },

        /**
        * @function
        *
        * Uploads file to the server. Get file from the `file` property.
        *
        */
        upload: function () {
            if (!this.file) {
                return;
            }

            this.$form.ajaxSubmit({
                beforeSend: this.xhrResetProgressBar,
                uploadProgress: this.xhrProgressHandler,
                complete: this.xhrCompleteHandler
            });
        },

        /**
        * @function
        *
        * Handle click event on `upload` button.
        *
        * @param {object} event Event object.
        *
        */
        clickHandler: function (event) {
            event.preventDefault();

            this.$input
                .val(null)
                // Show system upload window
                .trigger('click');
        },

        /**
        * @function
        *
        * Handle change event.
        *
        * @param {object} event Event object.
        *
        */
        changeHadler: function (event) {
            event.preventDefault();

            this.options.messenger.hideError();
            this.file = this.$input.get(0).files[0];

            // if file has valid file extension, than upload file.
            // Otherwise, show error message.
            if (this.checkExtValidity(this.file)) {
                this.upload();
            } else {
                this.options.messenger
                    .showError('Please select a file in .srt format.');
            }
        },

        /**
        * @function
        *
        * Checks that file has supported extension.
        *
        * @param {object} file Object with information about file.
        *
        * @returns {boolean} Indicate that file has supported or unsupported
        *                    extension.
        *
        */
        checkExtValidity: function (file) {
            if (!file.name) {
                return void(0);
            }

            var fileExtension = file.name
                                    .split('.')
                                    .pop()
                                    .toLowerCase();

            if ($.inArray(fileExtension, this.validFileExtensions) !== -1) {
                return true;
            }

            return false;
        },

        /**
        * @function
        *
        * Resets progress bar.
        *
        */
        xhrResetProgressBar: function () {
            var percentVal = '0%';

            this.$progress
                .width(percentVal)
                .html(percentVal)
                .removeClass(this.invisibleClass);
        },

        /**
        * @function
        *
        * Callback function to be invoked with upload progress information
        * (if supported by the browser).
        *
        * @param {object} event Event object.
        *
        * @param {integer} position Amount of transmitted bytes.
        * *
        * @param {integer} total Total size of file.
        * *
        * @param {integer} percentComplete Object with information about file.
        *
        */
        xhrProgressHandler: function (event, position, total, percentComplete) {
            var percentVal = percentComplete + '%';

            this.$progress
                .width(percentVal)
                .html(percentVal);
        },

        /**
        * @function
        *
        * Handle complete uploading.
        *
        */
        xhrCompleteHandler: function (xhr) {
            var utils = Transcripts.Utils,
                resp = JSON.parse(xhr.responseText),
                err = (resp.error) ? resp.error : 'Error: Uploading failed.',
                sub = resp.subs;

            this.$progress
                .addClass(this.invisibleClass);

            if (xhr.status === 200 && resp.status === "Success") {
                this.options.messenger.render('uploaded', resp);
                utils.Storage.set('sub', sub);
            } else {
                this.options.messenger.showError(err);
            }
        }
    });
}(this));
