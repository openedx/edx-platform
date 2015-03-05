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
            console.log(this);
            this.$el.html(this.template({
                sections: this.options.sections,
            }));
            var view = this;
            _.each(this.$('.account-settings-section-body'), function(section_el, index) {
                console.log(section_el);
                _.each(view.options.sections[index].fields, function(field, index) {
                    console.log(field);
                    $(section_el).append(field.view.el);
                });
            });
            return this;
        }
    });

    edx.student.account.ReadonlyFieldView = Backbone.View.extend({

        template: _.template($('#field_readonly-tpl').text()),

        events: {
        },

        initialize: function(options) {
        },

        render: function() {
            this.$el.html(this.template({
            }));
            return this;
        }
    });


}).call(this, $, _, Backbone, gettext);
