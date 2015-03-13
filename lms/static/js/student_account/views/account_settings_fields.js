var edx = edx || {};

(function($, _, Backbone, gettext) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};
    edx.student.account.fieldViews = edx.student.account.fieldViews || {};

    var messageRevertDelay = 4000;

    edx.student.account.fieldViews.FieldView = Backbone.View.extend({

        className: function() {
            return "account-settings-field " + "account-settings-field-" + (this.options.valueAttribute || this.options.id);
        },

        tagName: 'div',

        inProgressMessage: '<i class="fa fa-spinner"></i> Saving...' ,
        successMessage: '<i class="fa fa-check"></i> Successfully changed.',
        errorMessage: '<i class="fa fa-exclamation-triangle"></i> An error occurred, please try again.',

        initialize: function(options) {

            this.template = _.template($(this.templateSelector).text()),

            this.helpMessage = this.options.helpMessage || '';

            _.bindAll(this, 'modelValue', 'saveAttributes',
                        'message', 'showHelpMessage', 'showInProgressMessage', 'showSuccessMessage', 'showErrorMessage');
        },

        modelValue: function() {
            return this.model.get(this.options.valueAttribute);
        },

        saveAttributes: function(attributes, options) {
            var view = this;
            var defaultOptions = {
                contentType: 'application/merge-patch+json',
                patch: true,
                wait: true,
                success: function(model, response, options) { view.showSuccessMessage(response) },
                error: function(model, xhr, options) { view.showErrorMessage(xhr) },
            };
            this.showInProgressMessage();
            this.model.save(attributes, _.extend(defaultOptions, options));
        },

        message: function(message) {
            return this.$('.account-settings-field-message').html(message);
        },

        showHelpMessage: function() {
            this.message(this.options.helpMessage);
        },

        showInProgressMessage: function() {
            this.message(this.inProgressMessage);
        },

        showSuccessMessage: function(response) {
            this.message(this.successMessage);

            var view = this;
            var context = Date.now()
            this.lastSuccessMessageContext = context;
            setTimeout(function () {
                if ((context === view.lastSuccessMessageContext) && (view.message().html() == view.successMessage)) {
                    view.showHelpMessage();
                }
            }, messageRevertDelay);
        },

        showErrorMessage: function(xhr) {
            if (xhr.status === 400) {
                console.log(xhr.responseText);
                this.message(this.errorMessage);
            } else {
                this.message(this.errorMessage);
            }
        },
    });

    edx.student.account.fieldViews.ReadonlyFieldView = edx.student.account.fieldViews.FieldView.extend({

        templateSelector: '#field_readonly-tpl',

        initialize: function(options) {
            this._super(options);
            _.bindAll(this, 'render', 'updateValueInField');
            this.listenTo(this.model, "change:" + this.options.valueAttribute, this.updateValueInField);
        },

        render: function() {
            this.$el.html(this.template({
                title: this.options.title,
                value: this.modelValue(),
                message: this.helpMessage,
            }));
            return this;
        },

        updateValueInField: function() {
            this.$('.account-settings-field-value').html(this.modelValue());
        },
    });

    edx.student.account.fieldViews.TextFieldView = edx.student.account.fieldViews.FieldView.extend({

        templateSelector: '#field_text-tpl',

        events: {
            'change input': 'saveValue',
        },

        initialize: function(options) {
            this._super(options);
            _.bindAll(this, 'render', 'fieldValue', 'updateValueInField', 'saveValue');
            this.listenTo(this.model, "change:" + this.options.valueAttribute, this.updateValueInField);
        },

        render: function() {
            this.$el.html(this.template({
                title: this.options.title,
                value: this.modelValue(),
                message: this.helpMessage,
            }));
            return this;
        },

        fieldValue: function() {
            return this.$('.account-settings-field-value input').val();
        },

        updateValueInField: function() {
            this.$('.account-settings-field-value input').val(this.modelValue());
        },

        saveValue: function(event) {
            var attributes = {};
            attributes[this.options.valueAttribute] = this.fieldValue();
            this.saveAttributes(attributes);

        },
    });

    edx.student.account.fieldViews.DropdownFieldView = edx.student.account.fieldViews.FieldView.extend({

        templateSelector: '#field_dropdown-tpl',

        events: {
            'change select': 'saveValue',
        },

        initialize: function(options) {
            this._super(options);
            _.bindAll(this, 'render', 'fieldValue', 'updateValueInField', 'saveValue');
            this.listenTo(this.model, "change:" + this.options.valueAttribute, this.updateValueInField);
        },

        render: function() {
            this.$el.html(this.template({
                title: this.options.title,
                required: this.options.required,
                selectOptions: this.options.options,
                message: this.helpMessage,
            }));
            this.updateValueInField()
            return this;
        },

        fieldValue: function() {
            return this.$('.account-settings-field-value select').val();
        },

        updateValueInField: function() {
            var value;
            if (this.options.required) {
                value = this.modelValue() || this.options.defaultValue;
            } else {
                value = this.modelValue() || "";
            }
            this.$('.account-settings-field-value select').val(value);
        },

        saveValue: function() {
            var attributes = {};
            attributes[this.options.valueAttribute] = this.fieldValue();
            this.saveAttributes(attributes);

        },
    });

    edx.student.account.fieldViews.LinkFieldView = edx.student.account.fieldViews.FieldView.extend({

        templateSelector: '#field_link-tpl',

        events: {
            'click a': 'linkClicked',
        },

        initialize: function(options) {
            this._super(options);
            _.bindAll(this, 'render', 'linkClicked');
        },

        render: function() {
            this.$el.html(this.template({
                title: this.options.title,
                linkTitle: this.options.linkTitle,
                linkHref: this.options.linkHref,
                message: this.helpMessage,
            }));
            return this;
        },

        linkClicked: function() {
            event.preventDefault();
        },
    });

    edx.student.account.fieldViews.PasswordFieldView = edx.student.account.fieldViews.LinkFieldView.extend({

        initialize: function(options) {
            this._super(options);
            _.bindAll(this, 'resetPassword');
        },

        linkClicked: function(event) {
            event.preventDefault();
            this.resetPassword(event)
        },

        resetPassword: function(event) {
            var data = {};
            data[this.options.dataAttribute] = this.model.get(this.options.dataAttribute);

            var view = this;
            $.post(this.options.linkHref, data, function () {
                view.$('.account-settings-field-message').html("We have sent an email to your new address. Click the link.");
            });
        },

    });

}).call(this, $, _, Backbone, gettext);
