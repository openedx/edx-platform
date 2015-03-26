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
                        gettext('Your profile is set to limited because you have not set your birth year yet. Set it on the {account_settings_page_link}.'),
                        {'account_settings_page_link': '<a href="' + this.options.accountSettingsPageUrl + '">' + gettext('Account Settings page') + '</a>'}
                    ));
                } else {
                    this._super('');
                }
                return this._super();
            }
        });

        return LearnerProfileFieldViews;
    })
}).call(this, define || RequireJS.define);
