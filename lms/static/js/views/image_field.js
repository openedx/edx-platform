(function(define) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'backbone',
        'edx-ui-toolkit/js/utils/html-utils', 'js/views/fields',
        'text!templates/fields/field_image.underscore',
        'backbone-super', 'jquery.fileupload'
    ], function(gettext, $, _, Backbone, HtmlUtils, FieldViews, FieldImageTemplate) {
        var ImageFieldView = FieldViews.FieldView.extend({

            fieldType: 'image',

            fieldTemplate: FieldImageTemplate,
            uploadButtonSelector: '.upload-button-input',

            titleAdd: gettext('Upload an image'),
            titleEdit: gettext('Change image'),
            titleRemove: gettext('Remove'),

            titleUploading: gettext('Uploading'),
            titleRemoving: gettext('Removing'),

            titleImageAlt: '',
            screenReaderTitle: gettext('Image'),

            iconUpload: '<span class="icon fa fa-camera" aria-hidden="true"></span>',
            iconRemove: '<span class="icon fa fa-remove" aria-hidden="true"></span>',
            iconProgress: '<span class="icon fa fa-spinner fa-pulse fa-spin" aria-hidden="true"></span>',

            errorMessage: gettext('An error has occurred. Refresh the page, and then try again.'),

            events: {
                'click .u-field-upload-button': 'clickedUploadButton',
                'click .u-field-remove-button': 'clickedRemoveButton',
                'click .upload-submit': 'clickedUploadButton',
                'focus .upload-button-input': 'showHoverState',
                'blur .upload-button-input': 'hideHoverState'
            },

            initialize: function(options) {
                this.options = _.extend({}, options);
                this._super(options);
                _.bindAll(this, 'render', 'imageChangeSucceeded', 'imageChangeFailed', 'fileSelected',
                    'watchForPageUnload', 'onBeforeUnload');
            },

            render: function() {
                var attributes = {
                    id: this.options.valueAttribute,
                    inputName: (this.options.inputName || 'file'),
                    imageUrl: _.result(this, 'imageUrl'),
                    imageAltText: _.result(this, 'imageAltText'),
                    uploadButtonIcon: _.result(this, 'iconUpload'),
                    uploadButtonTitle: _.result(this, 'uploadButtonTitle'),
                    removeButtonIcon: _.result(this, 'iconRemove'),
                    removeButtonTitle: _.result(this, 'removeButtonTitle'),
                    screenReaderTitle: _.result(this, 'screenReaderTitle')
                };
                this.$el.html(HtmlUtils.HTML(this.template(attributes)).toString());
                this.delegateEvents();
                this.updateButtonsVisibility();
                this.watchForPageUnload();
                return this;
            },

            showHoverState: function() {
                this.$('.u-field-upload-button').addClass('button-visible');
            },

            hideHoverState: function() {
                this.$('.u-field-upload-button').removeClass('button-visible');
            },

            showErrorMessage: function(message) {
                return message;
            },

            imageUrl: function() {
                return '';
            },

            uploadButtonTitle: function() {
                if (this.isShowingPlaceholder()) {
                    return _.result(this, 'titleAdd');
                } else {
                    return _.result(this, 'titleEdit');
                }
            },

            removeButtonTitle: function() {
                return this.titleRemove;
            },

            isEditingAllowed: function() {
                return true;
            },

            isShowingPlaceholder: function() {
                return false;
            },

            setUploadButtonVisibility: function(state) {
                this.$('.u-field-upload-button').css('display', state);
            },

            setRemoveButtonVisibility: function(state) {
                this.$('.u-field-remove-button').css('display', state);
            },

            updateButtonsVisibility: function() {
                if (!this.isEditingAllowed() || !this.options.editable) {
                    this.setUploadButtonVisibility('none');
                }

                if (this.isShowingPlaceholder() || !this.options.editable) {
                    this.setRemoveButtonVisibility('none');
                }
            },

            clickedUploadButton: function() {
                $(this.uploadButtonSelector).fileupload({
                    url: this.options.imageUploadUrl,
                    type: 'POST',
                    add: this.fileSelected,
                    done: this.imageChangeSucceeded,
                    fail: this.imageChangeFailed
                });
            },

            clickedRemoveButton: function() {
                var view = this;
                this.setCurrentStatus('removing');
                this.setUploadButtonVisibility('none');
                this.showRemovalInProgressMessage();
                $.ajax({
                    type: 'POST',
                    url: this.options.imageRemoveUrl
                }).done(function() {
                    view.imageChangeSucceeded();
                }).fail(function(jqXHR) {
                    view.showImageChangeFailedMessage(jqXHR.status, jqXHR.responseText);
                });
            },

            imageChangeSucceeded: function() {
                this.$('.u-field-upload-button').removeClass('in-progress');
                this.render();
            },

            imageChangeFailed: function(e, data) {
            },

            showImageChangeFailedMessage: function(status, responseText) {
            },

            fileSelected: function(e, data) {
                if (_.isUndefined(data.files[0].size) || this.validateImageSize(data.files[0].size)) {
                    this.setCurrentStatus('uploading');
                    this.setRemoveButtonVisibility('none');
                    this.showUploadInProgressMessage();
                    data.submit();
                }
            },

            validateImageSize: function(imageBytes) {
                var humanReadableSize;
                if (imageBytes < this.options.imageMinBytes) {
                    humanReadableSize = this.bytesToHumanReadable(this.options.imageMinBytes);
                    this.showErrorMessage(
                        interpolate_text(
                            gettext('The file must be at least {size} in size.'), {size: humanReadableSize}
                        )
                    );
                    return false;
                } else if (imageBytes > this.options.imageMaxBytes) {
                    humanReadableSize = this.bytesToHumanReadable(this.options.imageMaxBytes);
                    this.showErrorMessage(
                        interpolate_text(
                            gettext('The file must be smaller than {size} in size.'), {size: humanReadableSize}
                        )
                    );
                    return false;
                }
                return true;
            },

            showUploadInProgressMessage: function() {
                this.$('.u-field-upload-button').addClass('in-progress');
                HtmlUtils.setHtml(this.$('.upload-button-icon'), HtmlUtils.HTML(this.iconProgress));
                HtmlUtils.setHtml(this.$('.upload-button-title'), HtmlUtils.HTML(this.titleUploading));
            },

            showRemovalInProgressMessage: function() {
                this.$('.u-field-remove-button').css('opacity', 1);
                HtmlUtils.setHtml(this.$('.remove-button-icon'), HtmlUtils.HTML(this.iconProgress));
                HtmlUtils.setHtml(this.$('.remove-button-title'), HtmlUtils.HTML(this.titleRemoving));
            },

            setCurrentStatus: function(status) {
                this.$('.image-wrapper').attr('data-status', status);
            },

            getCurrentStatus: function() {
                return this.$('.image-wrapper').attr('data-status');
            },

            watchForPageUnload: function() {
                $(window).on('beforeunload', this.onBeforeUnload);
            },

            onBeforeUnload: function() {
                var status = this.getCurrentStatus();
                if (status === 'uploading') {
                    return gettext('Upload is in progress. To avoid errors, stay on this page until the process is complete.');
                } else if (status === 'removing') {
                    return gettext('Removal is in progress. To avoid errors, stay on this page until the process is complete.');
                }
            },

            bytesToHumanReadable: function(size) {
                var units = [gettext('bytes'), gettext('KB'), gettext('MB')];
                var i = 0;
                while (size >= 1024) {
                    size /= 1024;
                    ++i;
                }
                return size.toFixed(1) * 1 + ' ' + units[i];
            }
        });

        return ImageFieldView;
    });
}).call(this, define || RequireJS.define);
