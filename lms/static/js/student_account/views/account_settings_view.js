var edx = edx || {};

(function($, _, Backbone, gettext) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.AccountSettingsView = Backbone.View.extend({

        events: {
        },

        initialize: function(options) {
            this.template = _.template($('#account_settings-tpl').text());
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


}).call(this, $, _, Backbone, gettext);
