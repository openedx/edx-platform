;(function (define, undefined) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'backbone', 'js/views/fields', 'js/vendor/backbone-super'
    ], function (gettext, $, _, Backbone, FieldViews) {

        var LearnerProfileFieldViews = {};

        LearnerProfileFieldViews.AccountPrivacyFieldView = FieldViews.DropdownFieldView.extend({

            render: function () {
                this._super();
                this.message();
                return this;
            },

            message: function () {
                if (this.profileIsPrivate) {
                    this._super(interpolate_text(
                        gettext("Your profile is disabled because you haven't filled in your Year of Birth. Please visit the Account Settings page. {account_settings_page_link}."),
                        {'account_settings_page_link': '<a href="' + this.options.accountSettingsPageUrl + '">' + gettext('Account Settings page') + '</a>'}
                    ));
                } else if (this.requiresParentalConsent) {
                    this._super(interpolate_text(
                        gettext('Your profile is disabled because you are under 14. If this is incorrect, please visit the Account Settings page. {account_settings_page_link}.'),
                        {'account_settings_page_link': '<a href="' + this.options.accountSettingsPageUrl + '">' + gettext('Account Settings page') + '</a>'}
                    ));
                }
                else {
                    this._super('');
                }
                return this._super();
            }
        });

        return LearnerProfileFieldViews;
    })
}).call(this, define || RequireJS.define);
