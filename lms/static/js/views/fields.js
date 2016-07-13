;(function (define, undefined) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'backbone', 
        'edx-ui-toolkit/js/utils/html-utils',
        'text!templates/fields/field_readonly.underscore',
        'text!templates/fields/field_dropdown.underscore',
        'text!templates/fields/field_link.underscore',
        'text!templates/fields/field_text.underscore',
        'text!templates/fields/field_textarea.underscore',
        'backbone-super'
    ], function (gettext, $, _, Backbone, HtmlUtils,
                 field_readonly_template,
                 field_dropdown_template,
                 field_link_template,
                 field_text_template,
                 field_textarea_template
    ) {

        var messageRevertDelay = 6000;
        var FieldViews = {};

        FieldViews.FieldView = Backbone.View.extend({
                
            fieldType: 'generic',

            className: function () {
                return 'u-field' + ' u-field-' + this.fieldType + ' u-field-' + this.options.valueAttribute;
            },

            tagName: 'div',

            indicators: {
                'canEdit': HtmlUtils.joinHtml(
                    HtmlUtils.HTML('<span class="icon fa fa-pencil message-can-edit" aria-hidden="true"></span><span class="sr">'), // jshint ignore:line
                    gettext("Editable"),
                    HtmlUtils.HTML('</span>')
                ),
                'error': HtmlUtils.joinHtml(
                    HtmlUtils.HTML('<span class="fa fa-exclamation-triangle message-error" aria-hidden="true"></span><span class="sr">'), // jshint ignore:line
                    gettext("Error"),
                    HtmlUtils.HTML('</span>')
                ),
                'validationError': HtmlUtils.joinHtml(
                    HtmlUtils.HTML('<span class="fa fa-exclamation-triangle message-validation-error" aria-hidden="true"></span><span class="sr">'), // jshint ignore:line
                    gettext("Validation Error"),
                    HtmlUtils.HTML('</span>')
                ),
                'inProgress': HtmlUtils.joinHtml(
                    HtmlUtils.HTML('<span class="fa fa-spinner fa-pulse message-in-progress" aria-hidden="true"></span><span class="sr">'), // jshint ignore:line
                    gettext("In Progress"),
                    HtmlUtils.HTML('</span>')
                ),
                'success': HtmlUtils.joinHtml(
                    HtmlUtils.HTML('<span class="fa fa-check message-success" aria-hidden="true"></span><span class="sr">'), // jshint ignore:line
                    gettext("Success"),
                    HtmlUtils.HTML('</span>')
                ),
                'plus': HtmlUtils.joinHtml(
                    HtmlUtils.HTML('<span class="fa fa-plus placeholder" aria-hidden="true"></span><span class="sr">'),
                    gettext("Placeholder"),
                    HtmlUtils.HTML('</span>')
                ),
            },

            messages: {
                'canEdit': '',
                'error': gettext('An error occurred. Please try again.'),
                'validationError': '',
                'inProgress': gettext('Saving'),
                'success': gettext('Your changes have been saved.')
            },

            constructor: function(options) {
                this.options = _.extend({}, options);
                Backbone.View.apply(this, arguments);
            },

            initialize: function () {

                this.template = _.template(this.fieldTemplate || '');

                this.helpMessage = this.options.helpMessage || '';
                this.showMessages = _.isUndefined(this.options.showMessages) ? true : this.options.showMessages;
                this.enabled = _.isUndefined(this.options.enabled) ? true: this.options.enabled;

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

            title: function (title) {
                return HtmlUtils.setHtml(this.$('.u-field-title'), title);
            },

            getMessage: function(message_status) {
                if ((message_status + 'Message') in this) {
                    return this[message_status + 'Message'].call(this);
                } else if (this.showMessages) {
                    return HtmlUtils.joinHtml(this.indicators[message_status], this.messages[message_status]);
                }
                return this.indicators[message_status];
            },

            showHelpMessage: function (message) {
                if (_.isUndefined(message) || _.isNull(message)) {
                    message = this.helpMessage;
                }
                this.$('.u-field-message-notification').html('');
                HtmlUtils.setHtml(this.$('.u-field-message-help'), message);
            },

            getNotificationMessage: function() {
                return HtmlUtils.HTML(this.$('.u-field-message-notification').html());
            },

            showNotificationMessage: function(message) {
                this.$('.u-field-message-help').html('');
                HtmlUtils.setHtml(this.$('.u-field-message-notification'), message);
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
                    location.reload(true);
                }

                var view = this;

                var context = Date.now();
                this.lastSuccessMessageContext = context;

                setTimeout(function () {
                    if ((context === view.lastSuccessMessageContext) &&
                        (view.getNotificationMessage().toString() === successMessage.toString())) {
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
                            validationErrorMessage = errors.field_errors[this.options.valueAttribute].user_message,
                            message = HtmlUtils.joinHtml(this.indicators.validationError, validationErrorMessage);
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
                this.persistChanges = _.isUndefined(options.persistChanges) ? false : options.persistChanges;
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
                if (this.persistChanges === true) {
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
                }
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
                var modelValue;
                if (this.persistChanges === false || this.mode !== 'edit') {return;}

                modelValue = this.modelValue();
                if (!(_.isUndefined(modelValue) || _.isNull(modelValue))) {
                    modelValue = modelValue.toString();
                }

                if (this.fieldValue() !== modelValue) {
                    this.saveValue();
                } else {
                    if (this.editable === 'always') {
                        this.showEditMode(true);
                    } else {
                        this.showDisplayMode(true);
                    }
                }
            },

            highlightFieldOnError: function () {
                this.$el.addClass('error');
            },

            unhighlightField: function () {
                this.$el.removeClass('error');
            }
        });

        FieldViews.ReadonlyFieldView = FieldViews.FieldView.extend({

            fieldType: 'readonly',

            fieldTemplate: field_readonly_template,

            initialize: function (options) {
                this._super(options);
                _.bindAll(this, 'render', 'fieldValue', 'updateValueInField');
                this.listenTo(this.model, "change:" + this.options.valueAttribute, this.updateValueInField);
            },

            render: function () {
                HtmlUtils.setHtml(this.$el, HtmlUtils.template(this.fieldTemplate)({
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
                return this.$('.u-field-value').text();
            },

            updateValueInField: function () {
                this.$('.u-field-value ').text(this.modelValue());
            }
        });

        FieldViews.TextFieldView = FieldViews.EditableFieldView.extend({

            fieldType: 'text',

            fieldTemplate: field_text_template,

            events: {
                'change input': 'saveValue'
            },

            initialize: function (options) {
                this._super(options);
                _.bindAll(this, 'render', 'fieldValue', 'updateValueInField', 'saveValue');
                this.listenTo(this.model, "change:" + this.options.valueAttribute, this.updateValueInField);
            },

            render: function () {
                HtmlUtils.setHtml(this.$el, HtmlUtils.template(this.fieldTemplate)({
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
                this.$('.u-field-value input').val(value);
            },

            saveValue: function () {
                var attributes = {};
                attributes[this.options.valueAttribute] = this.fieldValue();
                this.saveAttributes(attributes);
            }
        });

        FieldViews.DropdownFieldView = FieldViews.EditableFieldView.extend({

            fieldType: 'dropdown',

            fieldTemplate: field_dropdown_template,

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
                HtmlUtils.setHtml(this.$el, HtmlUtils.template(this.fieldTemplate)({
                    id: this.options.valueAttribute,
                    mode: this.mode,
                    editable: this.editable,
                    title: this.options.title,
                    screenReaderTitle: this.options.screenReaderTitle || this.options.title,
                    titleVisible: this.options.titleVisible !== undefined ? this.options.titleVisible : true,
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
                var value;
                if (this.editable === 'never') {
                    value = this.modelValueIsSet() ? this.modelValue () : null;
                }
                else {
                    value = this.$('.u-field-value select').val();
                }
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
                if (this.editable !== 'never') {
                    this.$('.u-field-value select').val(this.modelValue() || '');
                }

                var value = this.displayValue(this.modelValue() || '');
                if (this.modelValueIsSet() === false) {
                    value = this.options.placeholderValue || '';
                }
                this.$('.u-field-value').attr('aria-label', this.options.title);
                this.$('.u-field-value-readonly').text(value);

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
                if (this.editable !== 'never') {
                    this.$('.u-field-value select').prop('disabled', disable);
                }
            }
        });

        FieldViews.TextareaFieldView = FieldViews.EditableFieldView.extend({

            fieldType: 'textarea',

            fieldTemplate: field_textarea_template,

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
                HtmlUtils.setHtml(this.$el, HtmlUtils.template(this.fieldTemplate)({
                    id: this.options.valueAttribute,
                    screenReaderTitle: this.options.screenReaderTitle || this.options.title,
                    mode: this.mode,
                    editable: this.editable,
                    value: value,
                    message: this.helpMessage,
                    messagePosition: this.options.messagePosition || 'footer',
                    placeholderValue: this.options.placeholderValue
                }));
                this.delegateEvents();
                this.title((this.modelValue() || this.mode === 'edit') ?
                    this.options.title : HtmlUtils.joinHtml(this.indicators.plus, this.options.title));

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
                if (this.persistChanges === false) {return;}
                var textarea = this.$('textarea');
                textarea.css('height', 'auto').css('height', textarea.prop('scrollHeight') + 10);
            },

            modelValue: function() {
                var value = this._super();
                return value ? $.trim(value) : '';
            },

            fieldValue: function () {
                if (this.mode === 'edit') {
                    return this.$('.u-field-value textarea').val();
                }
                else {
                    return this.$('.u-field-value .u-field-value-readonly').text();
                }
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

            fieldTemplate: field_link_template,

            events: {
                'click a': 'linkClicked'
            },

            initialize: function (options) {
                this._super(options);
                _.bindAll(this, 'render', 'linkClicked');
            },

            render: function () {
                HtmlUtils.setHtml(this.$el, HtmlUtils.template(this.fieldTemplate)({
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

        return FieldViews;
    });
}).call(this, define || RequireJS.define);
