;(function (define, undefined) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'backbone', 'js/mustache', 'js/views/fields'
    ], function (gettext, $, _, Backbone, RequireMustache, FieldViews) {

        var AccountSettingsFieldViews = {};

        AccountSettingsFieldViews.EmailFieldView = FieldViews.TextFieldView.extend({

            successMessage: function() {
                return this.indicators.success + interpolate_text(
                    gettext(
                        'We\'ve sent a confirmation message to {new_email_address}. ' +
                        'Click the link in the message to update your email address.'
                    ),
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
                    success: function () {
                        view.showSuccessMessage();
                    },
                    error: function () {
                        view.showNotificationMessage(
                            view.indicators.error +
                                gettext('You must sign out and sign back in before your language changes take effect.')
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
                this.resetPassword(event);
            },

            resetPassword: function () {
                var data = {};
                data[this.options.emailAttribute] = this.model.get(this.options.emailAttribute);

                var view = this;
                $.ajax({
                    type: 'POST',
                    url: view.options.linkHref,
                    data: data,
                    success: function () {
                        view.showSuccessMessage();
                    },
                    error: function (xhr) {
                        view.showErrorMessage(xhr);
                    }
                });
            },

            successMessage: function () {
                return this.indicators.success + interpolate_text(
                    gettext(
                        'We\'ve sent a message to {email_address}. ' +
                        'Click the link in the message to reset your password.'
                    ),
                    {'email_address': this.model.get(this.options.emailAttribute)}
                );
            }
        });

        AccountSettingsFieldViews.LanguageProficienciesFieldView = FieldViews.DropdownFieldView.extend({

            modelValue: function () {
                var modelValue = this.model.get(this.options.valueAttribute);
                if (_.isArray(modelValue) && modelValue.length > 0) {
                    return modelValue[0].code;
                } else {
                    return null;
                }
            },

            saveValue: function () {
                var attributes = {},
                    value = this.fieldValue() ? [{'code': this.fieldValue()}] : [];
                attributes[this.options.valueAttribute] = value;
                this.saveAttributes(attributes);
            }

        });

        AccountSettingsFieldViews.AuthFieldView = FieldViews.LinkFieldView.extend({

            initialize: function (options) {
                this._super(options);
                _.bindAll(this, 'redirect_to', 'disconnect', 'successMessage', 'inProgressMessage');
            },

            render: function () {
                this.$el.html(this.template({
                    id: this.options.valueAttribute,
                    title: this.options.title,
                    screenReaderTitle: this.options.screenReaderTitle,
                    linkTitle: this.options.connected ? gettext('Unlink') : gettext('Link'),
                    linkHref: '',
                    message: this.helpMessage
                }));
                return this;
            },

            linkClicked: function (event) {
                event.preventDefault();

                this.showInProgressMessage();

                if (this.options.connected) {
                    this.disconnect();
                } else {
                    // Direct the user to the providers site to start the authentication process.
                    // See python-social-auth docs for more information.
                    this.redirect_to(this.options.connectUrl);
                }
            },

            redirect_to: function (url) {
                window.location.href = url;
            },

            disconnect: function () {
                var data = {};

                // Disconnects the provider from the user's edX account.
                // See python-social-auth docs for more information.
                var view = this;
                $.ajax({
                    type: 'POST',
                    url: this.options.disconnectUrl,
                    data: data,
                    dataType: 'html',
                    success: function () {
                        view.options.connected = false;
                        view.render();
                        view.showSuccessMessage();
                    },
                    error: function (xhr) {
                        view.showErrorMessage(xhr);
                    }
                });
            },

            inProgressMessage: function() {
                return this.indicators.inProgress + (this.options.connected ? gettext('Unlinking') : gettext('Linking'));
            },

            successMessage: function() {
                return this.indicators.success + gettext('Successfully unlinked.');
            }
        });

        return AccountSettingsFieldViews;
    });
}).call(this, define || RequireJS.define);
