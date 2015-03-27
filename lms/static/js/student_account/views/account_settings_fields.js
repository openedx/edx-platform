;(function (define, undefined) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'backbone', 'js/mustache', 'js/views/fields',
        'js/vendor/backbone-super'
    ], function (gettext, $, _, Backbone, RequireMustache, FieldViews) {

        var Mustache = window.Mustache || RequireMustache;

        var AccountSettingsFieldViews = {};

        AccountSettingsFieldViews.EmailFieldView = FieldViews.TextFieldView.extend({

            successMessage: function() {
                return this.indicators['success'] + interpolate_text(
                    gettext('We\'ve sent a confirmation message to {new_email_address}. Click the link in the message to update your email address.'),
                    {'new_email_address': this.fieldValue()}
                );
            }
        });

        AccountSettingsFieldViews.LanguagePreferenceFieldView = FieldViews.DropdownFieldView.extend({

            saveSucceeded: function () {
                var data = {
                    'language': this.modelValue()
                };

                var view = this;
                $.ajax({
                    type: 'POST',
                    url: '/i18n/setlang/',
                    data: data,
                    dataType: 'html',
                    success: function (data, status, xhr) {
                        view.showSuccessMessage();
                    },
                    error: function (xhr, status, error) {
                        view.message(
                            view.indicators['error'] + gettext('You must sign out of edX and sign back in before your language changes take effect.')
                        );
                    }
                });
            }

        });

        AccountSettingsFieldViews.PasswordFieldView = FieldViews.LinkFieldView.extend({

            initialize: function (options) {
                this._super(options);
                _.bindAll(this, 'resetPassword');
            },

            linkClicked: function (event) {
                event.preventDefault();
                this.resetPassword(event)
            },

            resetPassword: function (event) {
                var data = {};
                data[this.options.emailAttribute] = this.model.get(this.options.emailAttribute);

                var view = this;
                $.ajax({
                    type: 'POST',
                    url: view.options.linkHref,
                    data: data,
                    success: function (data, status, xhr) {
                        view.showSuccessMessage()
                    },
                    error: function (xhr, status, error) {
                        view.showErrorMessage(xhr);
                    }
                });
            },

            successMessage: function () {
                return this.indicators['success'] + interpolate_text(
                    gettext('We\'ve sent a message to {email_address}. Click the link in the message to reset your password.'),
                    {'email_address': this.model.get(this.options.emailAttribute)}
                );
            },
        });

        AccountSettingsFieldViews.LanguageProficienciesFieldView = FieldViews.DropdownFieldView.extend({

            modelValue: function () {
                var modelValue = this.model.get(this.options.valueAttribute);
                if (_.isArray(modelValue) && modelValue.length > 0) {
                    return modelValue[0].code
                } else {
                    return '';
                }
            },

            saveValue: function () {
                var attributes = {};
                var value = this.fieldValue() ? [{'code': this.fieldValue()}] : [];
                attributes[this.options.valueAttribute] = value;
                this.saveAttributes(attributes);
            }
        });

        return AccountSettingsFieldViews;
    })
}).call(this, define || RequireJS.define);
