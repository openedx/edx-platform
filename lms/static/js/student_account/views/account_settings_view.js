;(function (define, undefined) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'backbone', 'text!templates/student_account/account_settings.underscore'
    ], function (gettext, $, _, Backbone, accountSettingsTemplate) {

        var AccountSettingsView = Backbone.View.extend({

            initialize: function () {
                _.bindAll(this, 'render', 'renderFields', 'showLoadingError');
            },

            render: function () {
                this.$el.html(_.template(accountSettingsTemplate, {
                    sections: this.options.sectionsData
                }));
                return this;
            },

            renderFields: function () {
                this.$('.ui-loading-indicator').addClass('is-hidden');

                var view = this;
                _.each(this.$('.account-settings-section-body'), function (sectionEl, index) {
                    _.each(view.options.sectionsData[index].fields, function (field) {
                        $(sectionEl).append(field.view.render().el);
                    });
                });
                return this;
            },

            showLoadingError: function () {
                this.$('.ui-loading-indicator').addClass('is-hidden');
                this.$('.ui-loading-error').removeClass('is-hidden');
            }
        });

        return AccountSettingsView;
    });
}).call(this, define || RequireJS.define);
