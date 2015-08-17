;(function (define, undefined) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'backbone', 'js/mustache', 'backbone-super'
    ], function (gettext, $, _, Backbone, RequireMustache) {

        var Mustache = window.Mustache || RequireMustache;

        var messageRevertDelay = 6000;
        var FieldViews = {};

        FieldViews.FieldView = Backbone.View.extend({
                
            fieldType: 'generic',

            className: function () {
                return 'u-field' + ' u-field-' + this.fieldType + ' u-field-' + this.options.valueAttribute;
            },

            tagName: 'div',

            indicators: {
                'canEdit': '<i class="icon fa fa-pencil message-can-edit" aria-hidden="true"></i><span class="sr">' + gettext("Editable") + '</span>',
                'error': '<i class="fa fa-exclamation-triangle message-error" aria-hidden="true"></i><span class="sr">' + gettext("Error") + '</span>',
                'validationError': '<i class="fa fa-exclamation-triangle message-validation-error" aria-hidden="true"></i><span class="sr">' + gettext("Validation Error") + '</span>',
                'inProgress': '<i class="fa fa-spinner fa-pulse message-in-progress" aria-hidden="true"></i><span class="sr">' + gettext("In Progress") + '</span>',
                'success': '<i class="fa fa-check message-success" aria-hidden="true"></i><span class="sr">' + gettext("Success") + '</span>',
                'plus': '<i class="fa fa-plus placeholder" aria-hidden="true"></i><span class="sr">' + gettext("Placeholder")+ '</span>'
            },

            messages: {
                'canEdit': '',
                'error': gettext('An error occurred. Please try again.'),
                'validationError': '',
                'inProgress': gettext('Saving'),
                'success': gettext('Your changes have been saved.')
            },

            initialize: function () {

                this.template = _.template($(this.templateSelector).text());

                this.helpMessage = this.options.helpMessage || '';
                this.showMessages = _.isUndefined(this.options.showMessages) ? true : this.options.showMessages;

                _.bindAll(this, 'modelValue', 'modelValueIsSet', 'showNotificationMessage','getNotificationMessage',
                    'getMessage', 'title', 'showHelpMessage', 'showInProgressMessage', 'showSuccessMessage',
                    'showErrorMessage'
                );
            },

            modelValue: function () {
                return this.model.get(this.options.valueAttribute);
            },

            modelValueIsSet: function() {
                return (this.modelValue() === true);
            },

            title: function (text) {
                return this.$('.u-field-title').html(text);
            },

            getMessage: function(message_status) {
                if ((message_status + 'Message') in this) {
                    return this[message_status + 'Message'].call(this);
                } else if (this.showMessages) {
                    return this.indicators[message_status] + this.messages[message_status];
                }
                return this.indicators[message_status];
            },

            showHelpMessage: function (message) {
                if (_.isUndefined(message) || _.isNull(message)) {
                    message = this.helpMessage;
                }
                this.$('.u-field-message-notification').html('');
                this.$('.u-field-message-help').html(message);
            },

            getNotificationMessage: function() {
                return this.$('.u-field-message-notification').html();
            },

            showNotificationMessage: function(message) {
                this.$('.u-field-message-help').html('');
                this.$('.u-field-message-notification').html(message);
            },

            showCanEditMessage: function(show) {
                if (!_.isUndefined(show) && show) {
                    this.showNotificationMessage(this.getMessage('canEdit'));
                } else {
                    this.showNotificationMessage('');
                }
            },

            showInProgressMessage: function () {
                this.showNotificationMessage(this.getMessage('inProgress'));
            },

            showSuccessMessage: function () {
                var successMessage = this.getMessage('success');
                this.showNotificationMessage(successMessage);

                if (this.options.refreshPageOnSave) {
                    document.location.reload();
                }

                var view = this;

                var context = Date.now();
                this.lastSuccessMessageContext = context;

                setTimeout(function () {
                    if ((context === view.lastSuccessMessageContext) && (view.getNotificationMessage() === successMessage)) {
                        if (view.editable === 'toggle') {
                            view.showCanEditMessage(true);
                        } else {
                            view.showHelpMessage();
                        }
                    }
                }, messageRevertDelay);
            },

            showErrorMessage: function (xhr) {
                if (xhr.status === 400) {
                    try {
                        var errors = JSON.parse(xhr.responseText),
                            validationErrorMessage = Mustache.escapeHtml(
                                errors.field_errors[this.options.valueAttribute].user_message
                            ),
                            message = this.indicators.validationError + validationErrorMessage;
                        this.showNotificationMessage(message);
                    } catch (error) {
                        this.showNotificationMessage(this.getMessage('error'));
                    }
                } else {
                    this.showNotificationMessage(this.getMessage('error'));
                }
            }
        });

        FieldViews.EditableFieldView = FieldViews.FieldView.extend({

            initialize: function (options) {
                _.bindAll(this, 'saveAttributes', 'saveSucceeded', 'showDisplayMode', 'showEditMode',
                    'startEditing', 'finishEditing'
                );
                this._super(options);

                this.editable = _.isUndefined(this.options.editable) ? 'always': this.options.editable;
                this.$el.addClass('editable-' + this.editable);

                if (this.editable === 'always') {
                    this.showEditMode(false);
                } else {
                    this.showDisplayMode(false);
                }
            },

            saveAttributes: function (attributes, options) {
                var view = this;
                var defaultOptions = {
                    contentType: 'application/merge-patch+json',
                    patch: true,
                    wait: true,
                    success: function () {
                        view.saveSucceeded();
                    },
                    error: function (model, xhr) {
                        view.showErrorMessage(xhr);
                    }
                };
                this.showInProgressMessage();
                this.model.save(attributes, _.extend(defaultOptions, options));
            },

            saveSucceeded: function () {
                this.showSuccessMessage();
            },

            updateDisplayModeClass: function() {
                this.$el.removeClass('mode-edit');

                this.$el.toggleClass('mode-hidden', (this.editable === 'never' && !this.modelValueIsSet()));
                this.$el.toggleClass('mode-placeholder', (this.editable === 'toggle' && !this.modelValueIsSet()));
                this.$el.toggleClass('mode-display', (this.modelValueIsSet()));
            },

            showDisplayMode: function(render) {
                this.mode = 'display';
                if (render) { this.render(); }
                this.updateDisplayModeClass();
            },

            showEditMode: function(render) {
                this.mode = 'edit';
                if (render) { this.render(); }

                this.$el.removeClass('mode-hidden');
                this.$el.removeClass('mode-placeholder');
                this.$el.removeClass('mode-display');

                this.$el.addClass('mode-edit');
            },

            startEditing: function () {
                if (this.editable === 'toggle' && this.mode !== 'edit') {
                    this.showEditMode(true);
                }
            },

            finishEditing: function() {
                if (this.fieldValue() !== this.modelValue()) {
                    this.saveValue();
                } else {
                    if (this.editable === 'always') {
                        this.showEditMode(true);
                    } else {
                        this.showDisplayMode(true);
                    }
                }
            }
        });

        FieldViews.ReadonlyFieldView = FieldViews.FieldView.extend({

            fieldType: 'readonly',

            templateSelector: '#field_readonly-tpl',

            initialize: function (options) {
                this._super(options);
                _.bindAll(this, 'render', 'fieldValue', 'updateValueInField');
                this.listenTo(this.model, "change:" + this.options.valueAttribute, this.updateValueInField);
            },

            render: function () {
                this.$el.html(this.template({
                    id: this.options.valueAttribute,
                    title: this.options.title,
                    screenReaderTitle: this.options.screenReaderTitle || this.options.title,
                    value: this.modelValue(),
                    message: this.helpMessage
                }));
                this.delegateEvents();
                return this;
            },

            fieldValue: function () {
                return this.$('.u-field-value input').val();
            },

            updateValueInField: function () {
                this.$('.u-field-value input').val(Mustache.escapeHtml(this.modelValue()));
            }
        });

        FieldViews.TextFieldView = FieldViews.EditableFieldView.extend({

            fieldType: 'text',

            templateSelector: '#field_text-tpl',

            events: {
                'change input': 'saveValue'
            },

            initialize: function (options) {
                this._super(options);
                _.bindAll(this, 'render', 'fieldValue', 'updateValueInField', 'saveValue');
                this.listenTo(this.model, "change:" + this.options.valueAttribute, this.updateValueInField);
            },

            render: function () {
                this.$el.html(this.template({
                    id: this.options.valueAttribute,
                    title: this.options.title,
                    value: this.modelValue(),
                    message: this.helpMessage
                }));
                this.delegateEvents();
                return this;
            },

            fieldValue: function () {
                return this.$('.u-field-value input').val();
            },

            updateValueInField: function () {
                var value = (_.isUndefined(this.modelValue()) || _.isNull(this.modelValue())) ? '' : this.modelValue();
                this.$('.u-field-value input').val(Mustache.escapeHtml(value));
            },

            saveValue: function () {
                var attributes = {};
                attributes[this.options.valueAttribute] = this.fieldValue();
                this.saveAttributes(attributes);
            }
        });

        FieldViews.DropdownFieldView = FieldViews.EditableFieldView.extend({

            fieldType: 'dropdown',

            templateSelector: '#field_dropdown-tpl',

            events: {
                'click': 'startEditing',
                'change select': 'finishEditing',
                'focusout select': 'finishEditing'
            },

            initialize: function (options) {
                _.bindAll(this, 'render', 'optionForValue', 'fieldValue', 'displayValue', 'updateValueInField', 'saveValue');
                this._super(options);

                this.listenTo(this.model, "change:" + this.options.valueAttribute, this.updateValueInField);
            },

            render: function () {
                this.$el.html(this.template({
                    id: this.options.valueAttribute,
                    mode: this.mode,
                    title: this.options.title,
                    screenReaderTitle: this.options.screenReaderTitle || this.options.title,
                    titleVisible: this.options.titleVisible || true,
                    iconName: this.options.iconName,
                    showBlankOption: (!this.options.required || !this.modelValueIsSet()),
                    selectOptions: this.options.options,
                    message: this.helpMessage
                }));
                this.delegateEvents();
                this.updateValueInField();

                if (this.editable === 'toggle') {
                    this.showCanEditMessage(this.mode === 'display');
                }
                return this;
            },

            modelValueIsSet: function() {
                var value = this.modelValue();
                if (_.isUndefined(value) || _.isNull(value) || value === '') {
                    return false;
                } else {
                    return !(_.isUndefined(this.optionForValue(value)));
                }
            },

            optionForValue: function(value) {
                return _.find(this.options.options, function(option) { return option[0] === value; });
            },

            fieldValue: function () {
                var value = this.$('.u-field-value select').val();
                return value === '' ? null : value;
            },

            displayValue: function (value) {
                if (value) {
                    var option = this.optionForValue(value);
                    return (option ? option[1] : '');
                } else {
                    return '';
                }
            },

            updateValueInField: function () {
                this.$('.u-field-value select').val(this.modelValue() || '');

                var value = this.displayValue(this.modelValue() || '');
                if (this.modelValueIsSet() === false) {
                    value = this.options.placeholderValue || '';
                }
                this.$('.u-field-value').attr('aria-label', this.options.title);
                this.$('.u-field-value-readonly').html(Mustache.escapeHtml(value));

                if (this.mode === 'display') {
                    this.updateDisplayModeClass();
                }
            },

            saveValue: function () {
                var attributes = {};
                attributes[this.options.valueAttribute] = this.fieldValue();
                this.saveAttributes(attributes);
            },

            showDisplayMode: function(render) {
                this._super(render);
                if (this.editable === 'toggle') {
                    this.$('.u-field-value a').focus();
                }
            },

            showEditMode: function(render) {
                this._super(render);
                if (this.editable === 'toggle') {
                    this.$('.u-field-value select').focus();
                }
            },

            saveSucceeded: function() {
                if (this.editable === 'toggle') {
                    this.showDisplayMode();
                }

                if (this.options.required && this.modelValueIsSet()) {
                    this.$('option[value=""]').remove();
                }

                this._super();
            },

            disableField: function(disable) {
                this.$('.u-field-value select').prop('disabled', disable);
            }
        });

        FieldViews.TextareaFieldView = FieldViews.EditableFieldView.extend({

            fieldType: 'textarea',

            templateSelector: '#field_textarea-tpl',

            events: {
                'click .wrapper-u-field': 'startEditing',
                'click .u-field-placeholder': 'startEditing',
                'focusout textarea': 'finishEditing',
                'change textarea': 'adjustTextareaHeight',
                'keyup textarea': 'adjustTextareaHeight',
                'keydown textarea': 'onKeyDown',
                'paste textarea': 'adjustTextareaHeight',
                'cut textarea': 'adjustTextareaHeight'
            },

            initialize: function (options) {
                _.bindAll(this, 'render', 'onKeyDown', 'adjustTextareaHeight', 'fieldValue', 'saveValue', 'updateView');
                this._super(options);
                this.listenTo(this.model, "change:" + this.options.valueAttribute, this.updateView);
            },

            render: function () {
                var value = this.modelValue();
                if (this.mode === 'display') {
                    value = value || this.options.placeholderValue;
                }
                this.$el.html(this.template({
                    id: this.options.valueAttribute,
                    screenReaderTitle: this.options.screenReaderTitle || this.options.title,
                    mode: this.mode,
                    value: value,
                    message: this.helpMessage,
                    placeholderValue: this.options.placeholderValue
                }));
                this.delegateEvents();
                this.title((this.modelValue() || this.mode === 'edit') ? this.options.title : this.indicators['plus'] + this.options.title);

                if (this.editable === 'toggle') {
                    this.showCanEditMessage(this.mode === 'display');
                }
                return this;
            },

            onKeyDown: function (event) {
                if (event.keyCode === 13) {
                    event.preventDefault();
                    this.finishEditing(event);
                } else {
                    this.adjustTextareaHeight();
                }
            },

            adjustTextareaHeight: function() {
                var textarea = this.$('textarea');
                textarea.css('height', 'auto').css('height', textarea.prop('scrollHeight') + 10);
            },

            modelValue: function() {
                var value = this._super();
                return  value ? $.trim(value) : '';
            },

            fieldValue: function () {
                return this.$('.u-field-value textarea').val();
            },

            saveValue: function () {
                var attributes = {};
                attributes[this.options.valueAttribute] = this.fieldValue();
                this.saveAttributes(attributes);
            },

            updateView: function () {
                if (this.mode !== 'edit') {
                    this.showDisplayMode(true);
                }
            },

            modelValueIsSet: function() {
                return !(this.modelValue() === '');
            },

            showEditMode: function(render) {
                this._super(render);
                this.adjustTextareaHeight();
                this.$('.u-field-value textarea').focus();
            },

            saveSucceeded: function() {
                this._super();
                if (this.editable === 'toggle') {
                    this.showDisplayMode(true);
                    this.$('a').focus();
                }
            }
        });

        FieldViews.LinkFieldView = FieldViews.FieldView.extend({

            fieldType: 'link',

            templateSelector: '#field_link-tpl',

            events: {
                'click a': 'linkClicked'
            },

            initialize: function (options) {
                this._super(options);
                _.bindAll(this, 'render', 'linkClicked');
            },

            render: function () {
                this.$el.html(this.template({
                    id: this.options.valueAttribute,
                    title: this.options.title,
                    screenReaderTitle: this.options.screenReaderTitle || this.options.title,
                    linkTitle: this.options.linkTitle,
                    linkHref: this.options.linkHref,
                    message: this.helpMessage
                }));
                this.delegateEvents();
                return this;
            },

            linkClicked: function (event) {
                event.preventDefault();
            }
        });

        FieldViews.ImageFieldView = FieldViews.FieldView.extend({

            fieldType: 'image',

            templateSelector: '#field_image-tpl',
            uploadButtonSelector: '.upload-button-input',

            titleAdd: gettext("Upload an image"),
            titleEdit: gettext("Change image"),
            titleRemove: gettext("Remove"),

            titleUploading: gettext("Uploading"),
            titleRemoving: gettext("Removing"),

            titleImageAlt: '',
            screenReaderTitle: gettext("Image"),

            iconUpload: '<i class="icon fa fa-camera" aria-hidden="true"></i>',
            iconRemove: '<i class="icon fa fa-remove" aria-hidden="true"></i>',
            iconProgress: '<i class="icon fa fa-spinner fa-pulse fa-spin" aria-hidden="true"></i>',

            errorMessage: gettext("An error has occurred. Refresh the page, and then try again."),

            events: {
                'click .u-field-upload-button': 'clickedUploadButton',
                'click .u-field-remove-button': 'clickedRemoveButton',
                'click .upload-submit': 'clickedUploadButton',
                'focus .upload-button-input': 'showHoverState',
                'blur .upload-button-input': 'hideHoverState'
            },

            initialize: function (options) {
                this._super(options);
                _.bindAll(this, 'render', 'imageChangeSucceeded', 'imageChangeFailed', 'fileSelected',
                          'watchForPageUnload', 'onBeforeUnload');
            },

            render: function () {
                this.$el.html(this.template({
                    id: this.options.valueAttribute,
                    inputName: (this.options.inputName || 'file'),
                    imageUrl: _.result(this, 'imageUrl'),
                    imageAltText: _.result(this, 'imageAltText'),
                    uploadButtonIcon: _.result(this, 'iconUpload'),
                    uploadButtonTitle: _.result(this, 'uploadButtonTitle'),
                    removeButtonIcon: _.result(this, 'iconRemove'),
                    removeButtonTitle: _.result(this, 'removeButtonTitle'),
                    screenReaderTitle: _.result(this, 'screenReaderTitle')
                }));
                this.delegateEvents();
                this.updateButtonsVisibility();
                this.watchForPageUnload();
                return this;
            },

            showHoverState: function () {
                this.$('.u-field-upload-button').addClass('button-visible');
            },

            hideHoverState: function () {
                this.$('.u-field-upload-button').removeClass('button-visible');
            },

            showErrorMessage: function (message) {
                return message;
            },

            imageUrl: function () {
                return '';
            },

            uploadButtonTitle: function () {
                if (this.isShowingPlaceholder()) {
                    return _.result(this, 'titleAdd');
                } else {
                    return _.result(this, 'titleEdit');
                }
            },

            removeButtonTitle: function () {
                return this.titleRemove;
            },

            isEditingAllowed: function () {
                return true;
            },

            isShowingPlaceholder: function () {
                return false;
            },

            setUploadButtonVisibility: function (state) {
                this.$('.u-field-upload-button').css('display', state);
            },

            setRemoveButtonVisibility: function (state) {
                this.$('.u-field-remove-button').css('display', state);
            },

            updateButtonsVisibility: function () {
                if (!this.isEditingAllowed() || !this.options.editable) {
                    this.setUploadButtonVisibility('none');
                }

                if (this.isShowingPlaceholder() || !this.options.editable) {
                    this.setRemoveButtonVisibility('none');
                }
            },

            clickedUploadButton: function () {
                $(this.uploadButtonSelector).fileupload({
                    url: this.options.imageUploadUrl,
                    type: 'POST',
                    add: this.fileSelected,
                    done: this.imageChangeSucceeded,
                    fail: this.imageChangeFailed
                });
            },

            clickedRemoveButton: function () {
                var view = this;
                this.setCurrentStatus('removing');
                this.setUploadButtonVisibility('none');
                this.showRemovalInProgressMessage();
                $.ajax({
                    type: 'POST',
                    url: this.options.imageRemoveUrl
                }).done(function () {
                    view.imageChangeSucceeded();
                }).fail(function (jqXHR) {
                    view.showImageChangeFailedMessage(jqXHR.status, jqXHR.responseText);
                });
            },

            imageChangeSucceeded: function () {
                this.render();
            },

            imageChangeFailed: function (e, data) {
            },

            showImageChangeFailedMessage: function (status, responseText) {
            },

            fileSelected: function (e, data) {
                if (_.isUndefined(data.files[0].size) || this.validateImageSize(data.files[0].size)) {
                    this.setCurrentStatus('uploading');
                    this.setRemoveButtonVisibility('none');
                    this.showUploadInProgressMessage();
                    data.submit();
                }
            },

            validateImageSize: function (imageBytes) {
                var humanReadableSize;
                if (imageBytes < this.options.imageMinBytes) {
                    humanReadableSize = this.bytesToHumanReadable(this.options.imageMinBytes);
                    this.showErrorMessage(
                        interpolate_text(
                            gettext("The file must be at least {size} in size."), {size: humanReadableSize}
                        )
                    );
                    return false;
                } else if (imageBytes > this.options.imageMaxBytes) {
                    humanReadableSize = this.bytesToHumanReadable(this.options.imageMaxBytes);
                    this.showErrorMessage(
                        interpolate_text(
                            gettext("The file must be smaller than {size} in size."), {size: humanReadableSize}
                        )
                    );
                    return false;
                }
                return true;
            },

            showUploadInProgressMessage: function () {
                this.$('.u-field-upload-button').css('opacity', 1);
                this.$('.upload-button-icon').html(this.iconProgress);
                this.$('.upload-button-title').html(this.titleUploading);
            },

            showRemovalInProgressMessage: function () {
                this.$('.u-field-remove-button').css('opacity', 1);
                this.$('.remove-button-icon').html(this.iconProgress);
                this.$('.remove-button-title').html(this.titleRemoving);
            },

            setCurrentStatus: function (status) {
                this.$('.image-wrapper').attr('data-status', status);
            },

            getCurrentStatus: function () {
                return this.$('.image-wrapper').attr('data-status');
            },

            watchForPageUnload: function () {
                $(window).on('beforeunload', this.onBeforeUnload);
            },

            onBeforeUnload: function () {
                var status = this.getCurrentStatus();
                if (status === 'uploading') {
                    return gettext("Upload is in progress. To avoid errors, stay on this page until the process is complete.");
                } else if (status === 'removing') {
                    return gettext("Removal is in progress. To avoid errors, stay on this page until the process is complete.");
                }
            },

            bytesToHumanReadable: function (size) {
                var units = [gettext('bytes'), gettext('KB'), gettext('MB')];
                var i = 0;
                while(size >= 1024) {
                    size /= 1024;
                    ++i;
                }
                return size.toFixed(1)*1 + ' ' + units[i];
            }
        });

        return FieldViews;
    });
}).call(this, define || RequireJS.define);
