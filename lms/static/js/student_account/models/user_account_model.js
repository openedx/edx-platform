;(function (define, undefined) {
    'use strict';
    define([
        'gettext', 'underscore', 'backbone',
    ], function (gettext, _, Backbone) {

        var UserAccountModel = Backbone.Model.extend({
            idAttribute: 'username',
            defaults: {
                username: '',
                name: '',
                email: '',
                password: '',
                language: null,
                country: null,
                date_joined: "",
                gender: null,
                goals: "",
                level_of_education: null,
                mailing_address: "",
                year_of_birth: null,
                bio: null,
                default_public_account_fields: []
            },

            parse : function(response, xhr) {
                if (_.isNull(response)) {
                    return {};
                }

                // Currently when a non-staff user A access user B's profile, the only way to tell whether user B's
                // profile is public is to check if the api has returned fields other than the default public fields
                // specified in settings.ACCOUNT_VISIBILITY_CONFIGURATION.
                var profileIsPublic = _.size(_.difference(_.keys(response), this.get('default_public_account_fields'))) > 0;
                this.set({'profile_is_public': profileIsPublic}, { silent: true });

  	            return response;
            }
        });

        return UserAccountModel;
    })
}).call(this, define || RequireJS.define);
