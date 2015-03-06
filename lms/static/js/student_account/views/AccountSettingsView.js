var edx = edx || {};

(function($, _, Backbone, gettext) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.AccountSettingsView = Backbone.View.extend({

        template: _.template($('#account_settings-tpl').text()),

        events: {
        },

        initialize: function(options) {
        },

        render: function() {
            this.$el.html(this.template({
                sections: this.options.sections,
            }));

            var view = this;
            _.each(this.$('.account-settings-section-body'), function(section_el, index) {
                _.each(view.options.sections[index].fields, function(field, index) {
                    $(section_el).append(field.view.el);
                });
            });
            return this;
        }
    });

    edx.student.account.FieldView = Backbone.View.extend({

        className: "account-settings-field",
        tagName: "div",

    });

    edx.student.account.ReadonlyFieldView = edx.student.account.FieldView.extend({

        template: _.template($('#field_readonly-tpl').text()),

        events: {

        },

        initialize: function(options) {
            this.listenTo(this.model, "change", this.render);
        },

        render: function() {
            this.$el.html(this.template({
                title: this.options.title,
                value: this.model[this.options.attribute],
                message: this.options.message,
            }));
            return this;
        }
    });

    edx.student.account.TextFieldView = edx.student.account.FieldView.extend({

        template: _.template($('#field_text-tpl').text()),

        events: {

        },

        initialize: function(options) {
            this.listenTo(this.model, "change", this.render);
        },

        render: function() {
            this.$el.html(this.template({
                title: this.options.title,
                value: this.model[this.options.attribute],
                message: this.options.message,
            }));
            return this;
        }
    });

    edx.student.account.LinkFieldView = edx.student.account.FieldView.extend({

        template: _.template($('#field_link-tpl').text()),

        events: {

        },

        initialize: function(options) {
            this.listenTo(this.model, "change", this.render);
        },

        render: function() {
            this.$el.html(this.template({
                title: this.options.title,
                link_title: this.options.link_title,
                link_href: this.options.link_href,
                message: this.options.message,
            }));
            return this;
        }
    });

    edx.student.account.DropdownFieldView = edx.student.account.FieldView.extend({

        template: _.template($('#field_dropdown-tpl').text()),

        events: {

        },

        initialize: function(options) {
            this.listenTo(this.model, "change", this.render);
        },

        render: function() {
            this.$el.html(this.template({
                title: this.options.title,
                message: this.options.message,
            }));
            return this;
        }
    });

}).call(this, $, _, Backbone, gettext);
