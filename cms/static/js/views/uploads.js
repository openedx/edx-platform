define(['jquery', 'underscore', 'gettext', 'js/views/modals/base_modal', 'edx-ui-toolkit/js/utils/html-utils',
    'jquery.form'],
function($, _, gettext, BaseModal, HtmlUtils) {
    'use strict';
    var UploadDialog = BaseModal.extend({
        events: _.extend({}, BaseModal.prototype.events, {
            'change input[type=file]': 'selectFile',
            'click .action-upload': 'upload'
        }),

        options: $.extend({}, BaseModal.prototype.options, {
            modalName: 'assetupload',
            modalSize: 'med',
            successMessageTimeout: 2000, // 2 seconds
            viewSpecificClasses: 'confirm'
        }),

        initialize: function(options) {
            BaseModal.prototype.initialize.call(this);
            this.template = this.loadTemplate('upload-dialog');
            this.listenTo(this.model, 'change', this.renderContents);
            this.options.title = this.model.get('title');
            // `uploadData` can contain extra data that
            // can be POSTed along with the file.
            this.uploadData = _.extend({}, options.uploadData);
        },

        addActionButtons: function() {
            this.addActionButton('upload', gettext('Upload'), true);
            BaseModal.prototype.addActionButtons.call(this);
        },

        renderContents: function() {
            var isValid = this.model.isValid(),
                selectedFile = this.model.get('selectedFile'),
                oldInput = this.$('input[type=file]');
            BaseModal.prototype.renderContents.call(this);
            // Ideally, we'd like to tell the browser to pre-populate the
            // <input type="file"> with the selectedFile if we have one -- but
            // browser security prohibits that. So instead, we'll swap out the
            // new input (that has no file selected) with the old input (that
            // already has the selectedFile selected). However, we only want to do
            // this if the selected file is valid: if it isn't, we want to render
            // a blank input to prompt the user to upload a different (valid) file.
            if (selectedFile && isValid) {
                $(oldInput).removeClass('error');
                this.$('input[type=file]').replaceWith(HtmlUtils.HTML(oldInput).toString());
                this.$('.action-upload').removeClass('disabled');
            } else {
                this.$('.action-upload').addClass('disabled');
            }
            return this;
        },

        getContentHtml: function() {
            return this.template({
                url: this.options.url || CMS.URL.UPLOAD_ASSET,
                message: this.model.get('message'),
                selectedFile: this.model.get('selectedFile'),
                uploading: this.model.get('uploading'),
                uploadedBytes: this.model.get('uploadedBytes'),
                totalBytes: this.model.get('totalBytes'),
                finished: this.model.get('finished'),
                error: this.model.validationError
            });
        },

        selectFile: function(e) {
            var selectedFile = e.target.files[0] || null;
            this.model.set({
                selectedFile: selectedFile
            });
            // This change event triggering necessary for FireFox, because the browser don't
            // consider change of File object (file input field) as a change in model.
            if (selectedFile && $.isEmptyObject(this.model.changed)) {
                this.model.trigger('change');
            }
        },

        upload: function(e) {
            var uploadAjaxData = _.extend({}, this.uploadData);
            // don't show the generic error notification; we're in a modal,
            // and we're better off modifying it instead.
            uploadAjaxData.notifyOnError = false;

            if (e && e.preventDefault) { e.preventDefault(); }
            this.model.set('uploading', true);
            this.$('form').ajaxSubmit({
                success: _.bind(this.success, this),
                error: _.bind(this.error, this),
                uploadProgress: _.bind(this.progress, this),
                data: uploadAjaxData
            });
        },

        progress: function(event, position, total) {
            this.model.set({
                uploadedBytes: position,
                totalBytes: total
            });
        },

        success: function(response, statusText, xhr, form) {
            this.model.set({
                uploading: false,
                finished: true
            });
            if (this.options.onSuccess) {
                this.options.onSuccess(response, statusText, xhr, form);
            }
            var that = this;
            this.removalTimeout = setTimeout(function() {
                that.hide();
            }, this.options.successMessageTimeout);
        },

        error: function() {
            this.model.set({
                uploading: false,
                uploadedBytes: 0,
                title: gettext("We're sorry, there was an error")
            });
        }
    });
    return UploadDialog;
}); // end define()
