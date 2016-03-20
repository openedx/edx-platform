;(function(define, undefined) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'backbone', 'js/views/fields',
        'edx-ui-toolkit/js/utils/html-utils'
    ], function(gettext, $, _, Backbone, FieldViews, HtmlUtils) {

        var AccountSettingsFieldViews = {};

        AccountSettingsFieldViews.EmailFieldView = FieldViews.TextFieldView.extend({
            successMessage: function() {
                return HtmlUtils.interpolateHtml(
                    gettext(
                        '{success_indicator}We\'ve sent a confirmation message to {new_email_address}. Click the link in the message to update your email address.'  // jshint ignore:line
                    ),
                    {success_indicator: this.indicators.success, new_email_address: this.fieldValue()}
                );
            }
        });

        AccountSettingsFieldViews.LanguagePreferenceFieldView = FieldViews.DropdownFieldView.extend({

            saveSucceeded: function() {
                var data = {
                    'language': this.modelValue()
                };

                var view = this;
                $.ajax({
                    type: 'POST',
                    url: '/i18n/setlang/',
                    data: data,
                    dataType: 'html',
                    success: function() {
                        view.showSuccessMessage();
                    },
                    error: function() {
                        view.showNotificationMessage(
                            HtmlUtils.interpolateHtml(
                                gettext('{error_indicator}You must sign out and sign back in before your language changes take effect.'),  // jshint ignore:line
                                {error_indicator: view.indicators.error}
                            )
                        );
                    }
                });
            }

        });

        AccountSettingsFieldViews.PasswordFieldView = FieldViews.LinkFieldView.extend({

            initialize: function(options) {
                this._super(options);
                _.bindAll(this, 'resetPassword');
            },

            linkClicked: function(event) {
                event.preventDefault();
                this.resetPassword(event);
            },

            resetPassword: function() {
                var data = {},
                    view = this;
                data[this.options.emailAttribute] = this.model.get(this.options.emailAttribute);
                $.ajax({
                    type: 'POST',
                    url: view.options.linkHref,
                    data: data,
                    success: function() {
                        view.showSuccessMessage();
                    },
                    error: function(xhr) {
                        view.showErrorMessage(xhr);
                    }
                });
            },

            successMessage: function() {
                return HtmlUtils.interpolateHtml(
                    gettext(
                        '{success_indicator}We\'ve sent a message to {email_address}. Click the link in the message to reset your password.'  // jshint ignore:line
                    ),
                    {
                        success_indicator: this.indicators.success,
                        email_address: this.model.get(this.options.emailAttribute)
                    }
                );
            }
        });

        AccountSettingsFieldViews.LanguageProficienciesFieldView = FieldViews.DropdownFieldView.extend({
            modelValue: function() {
                var modelValue = this.model.get(this.options.valueAttribute);
                if (_.isArray(modelValue) && modelValue.length > 0) {
                    return modelValue[0].code;
                } else {
                    return null;
                }
            },

            saveValue: function() {
                var attributes = {},
                    value = this.fieldValue() ? [{'code': this.fieldValue()}] : [];
                if (this.persistChanges === true) {
                    attributes[this.options.valueAttribute] = value;
                    this.saveAttributes(attributes);
                }
            }
        });

        AccountSettingsFieldViews.AuthFieldView = FieldViews.LinkFieldView.extend({

            initialize: function(options) {
                this._super(options);
                _.bindAll(this, 'redirect_to', 'disconnect', 'successMessage', 'inProgressMessage');
            },

            render: function() {
                var linkTitle;
                if (this.options.connected) {
                    linkTitle = gettext('Unlink');
                } else if (this.options.acceptsLogins) {
                    linkTitle = gettext('Link');
                } else {
                    linkTitle = '';
                }

                this.$el.html(this.template({
                    id: this.options.valueAttribute,
                    title: this.options.title,
                    screenReaderTitle: this.options.screenReaderTitle,
                    linkTitle: linkTitle,
                    linkHref: '',
                    message: this.helpMessage
                }));
                return this;
            },

            linkClicked: function(event) {
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

            redirect_to: function(url) {
                window.location.href = url;
            },

            disconnect: function() {
                var data = {};

                // Disconnects the provider from the user's edX account.
                // See python-social-auth docs for more information.
                var view = this;
                $.ajax({
                    type: 'POST',
                    url: this.options.disconnectUrl,
                    data: data,
                    dataType: 'html',
                    success: function() {
                        view.options.connected = false;
                        view.render();
                        view.showSuccessMessage();
                    },
                    error: function(xhr) {
                        view.showErrorMessage(xhr);
                    }
                });
            },

            inProgressMessage: function() {
                return HtmlUtils.interpolateHtml(
                    this.options.connected ?
                        gettext('{in_progress_indicator}Unlinking') :
                        gettext('{in_progress_indicator}Linking'),
                    {in_progress_indicator: this.indicators.inProgress}
                );
            },

            successMessage: function() {
                return HtmlUtils.interpolateHtml(
                    gettext('{success_indicator}Successfully unlinked.'),
                    {success_indicator: this.indicators.success}
                );
            }
        });

        return AccountSettingsFieldViews;
    });
}).call(this, define || RequireJS.define);
