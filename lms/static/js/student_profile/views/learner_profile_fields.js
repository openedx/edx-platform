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
                        gettext("You must specify your birth year before you can share your full profile. To specify your birth year, go to the {account_settings_page_link}"),
                        {'account_settings_page_link': '<a href="' + this.options.accountSettingsPageUrl + '">' + gettext('Account Settings page.') + '</a>'}
                    ));
                } else if (this.requiresParentalConsent) {
                    this._super(interpolate_text(
                        gettext('You must be over 13 to share a full profile. If you are over 13, make sure that you have specified a birth year on the {account_settings_page_link}'),
                        {'account_settings_page_link': '<a href="' + this.options.accountSettingsPageUrl + '">' + gettext('Account Settings page.') + '</a>'}
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
