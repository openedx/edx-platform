var edx = edx || {};

(function($, _, Backbone, gettext) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};
    edx.student.account.settingsViews = edx.student.account.settingsViews || {};

    edx.student.account.settingsViews.AccountSettingsView = Backbone.View.extend({

        template: _.template($('#account_settings-tpl').text()),

        events: {
        },

        initialize: function(options) {
            _.bindAll(this, 'render', 'setupFields');
        },

        modelValue: function() {
            return this.model.get(this.options.valueAttribute);
        },

        render: function() {
            this.$el.html(this.template({
                sections: this.options.sections
            }));
            return this;
        },

        setupFields: function() {
            this.$('.ui-loading-anim').addClass('is-hidden');

            var view = this;
            _.each(this.$('.account-settings-section-body'), function(sectionEl, index) {
                _.each(view.options.sections[index].fields, function(field, index) {
                    $(sectionEl).append(field.view.render().el);
                });
            });
            return this;
        }
    });

    edx.student.account.settingsViews.FieldView = Backbone.View.extend({

        className: function(){
            return "account-settings-field " + this.options.valueAttribute;
        },
        tagName: "div",

        initialize: function(options) {
            _.bindAll(this, 'modelValue');
        },

        modelValue: function() {
            return this.model.get(this.options.valueAttribute);
        }

    });

    edx.student.account.settingsViews.ReadonlyFieldView = edx.student.account.settingsViews.FieldView.extend({

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

    edx.student.account.settingsViews.TextFieldView = edx.student.account.settingsViews.FieldView.extend({

        template: _.template($('#field_text-tpl').text()),

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
            this.$('.account-settings-field-value input').val(this.modelValue());
        },
    });

    edx.student.account.settingsViews.LinkFieldView = edx.student.account.settingsViews.FieldView.extend({

        template: _.template($('#field_link-tpl').text()),

        events: {

        },

        initialize: function(options) {
            _.bindAll(this, 'render', 'updateValue');
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
    });

    edx.student.account.settingsViews.DropdownFieldView = edx.student.account.settingsViews.FieldView.extend({

        template: _.template($('#field_dropdown-tpl').text()),

        events: {

        },

        initialize: function(options) {
            _.bindAll(this, 'render', 'updateValue');
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

        updateValue: function() {
            var value;
            if (this.options.required) {
                value = this.modelValue() || this.options.defaultValue;
            } else {
                value = this.modelValue() || "";
            }
            this.$(".account-settings-field-value select").val((value));
        },
    });

}).call(this, $, _, Backbone, gettext);
