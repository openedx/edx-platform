var edx = edx || {};

(function($, _, Backbone, gettext) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};
    edx.student.account.fieldViews = edx.student.account.fieldViews || {};

    edx.student.account.fieldViews.FieldView = Backbone.View.extend({

        className: function(){
            return "account-settings-field " + this.options.valueAttribute;
        },
        tagName: "div",

        errorMessage: "An error occurred",
        successMessage: "Successfully Changed",

        initialize: function(options) {
            _.bindAll(this, 'modelValue', 'saveToServer');
        },

        modelValue: function() {
            return this.model.get(this.options.valueAttribute);
        },

        saveToServer: function(attributes, options) {
            var view = this;
            var defaultOptions = {
                contentType: 'application/merge-patch+json',
                patch:true,
                wait: true,
                success: function(model, response, options) {
                    view.$('.account-settings-field-message').html(view.successMessage);
                },
                error: function(model, xhr, options) {
                    if (xhr.status === 400) {
                        view.$('.account-settings-field-message').html("Wrong input");
                    } else {
                        view.$('.account-settings-field-message').html(view.errorMessage);
                    }
                }
            };
            this.model.save(attributes, _.extend(defaultOptions, options));
        }
    });

    edx.student.account.fieldViews.ReadonlyFieldView = edx.student.account.fieldViews.FieldView.extend({

        template: _.template($('#field_readonly-tpl').text()),

        events: {

        },

        initialize: function(options) {
            _.bindAll(this, 'render', 'updateValue');
            this.listenTo(this.model, "change:" + this.options.valueAttribute, this.updateValue);
        },

        render: function() {
            this.$el.html(this.template({
                title: this.options.title,
                value: this.modelValue(),
                message: this.options.message,
            }));
            return this;
        },

        updateValue: function() {
            this.$('.account-settings-field-value').html(this.modelValue());
        },
    });

    edx.student.account.fieldViews.TextFieldView = edx.student.account.fieldViews.FieldView.extend({

        template: _.template($('#field_text-tpl').text()),

        events: {
            'change input'      : 'saveValue',
            'keyup input'       : function(event) { if (event.keyCode == 13) { this.saveValue(); } }
        },

        initialize: function(options) {
            _.bindAll(this, 'render', 'fieldValue', 'updateValue', 'saveValue');
            this.listenTo(this.model, "change:" + this.options.valueAttribute, this.updateValue);
        },

        render: function() {
            this.$el.html(this.template({
                title: this.options.title,
                value: this.modelValue(),
                message: this.options.message,
            }));
            return this;
        },

        fieldValue: function() {
            return this.$('.account-settings-field-value input').val();
        },

        updateValue: function() {
            this.$('.account-settings-field-value input').val(this.modelValue());
        },

        saveValue: function(event) {
            var attributes = {};
            attributes[this.options.valueAttribute] = this.fieldValue();
            this.saveToServer(attributes);

        },
    });

    edx.student.account.fieldViews.LinkFieldView = edx.student.account.fieldViews.FieldView.extend({

        template: _.template($('#field_link-tpl').text()),

        events: {
            'click a' : 'resetPassword',
        },

        initialize: function(options) {
            _.bindAll(this, 'render', 'updateValue', 'resetPassword');
            this.listenTo(this.model, "change", this.updateValue);
        },

        render: function() {
            this.$el.html(this.template({
                title: this.options.title,
                linkTitle: this.options.linkTitle,
                linkHref: this.options.linkHref,
                message: this.options.message,
            }));
            return this;
        },

        updateValue: function() {
        },

        resetPassword: function(e) {
            e.preventDefault();
            var view = this;
            var data = {};
            data[this.options.dataAttribute] = this.model.get(this.options.dataAttribute);
            $.post(this.options.linkHref, data, function () {
                view.$('.account-settings-field-message').html("We have sent an email to your new address. Click the link.");
            });
        },

    });

    edx.student.account.fieldViews.DropdownFieldView = edx.student.account.fieldViews.FieldView.extend({

        template: _.template($('#field_dropdown-tpl').text()),

        events: {
            'change select'      : 'saveValue',
        },

        initialize: function(options) {
            _.bindAll(this, 'render', 'updateValue', 'fieldValue', 'saveValue');
            this.listenTo(this.model, "change:" + this.options.valueAttribute, this.updateValue);
        },

        render: function() {
            this.$el.html(this.template({
                title: this.options.title,
                required: this.options.required,
                selectOptions: this.options.options,
                message: this.options.message,
            }));
            this.updateValue()
            return this;
        },

        fieldValue: function() {
            return this.$('.account-settings-field-value select').val();
        },
        updateValue: function() {
            var value;
            if (this.options.required) {
                value = this.modelValue() || this.options.defaultValue;
            } else {
                value = this.modelValue() || "";
            }
            this.$(".account-settings-field-value select").val((value));
        },

        saveValue: function() {
            var attributes = {};
            attributes[this.options.valueAttribute] = this.fieldValue();
            this.saveToServer(attributes);

        },
    });

}).call(this, $, _, Backbone, gettext);
