/* eslint-disable-next-line no-shadow-restricted-names, no-unused-vars */
(function(define, undefined) {
    'use strict';

    define([
        'gettext', 'underscore', 'backbone'
    ], function(gettext, _, Backbone) {
        // eslint-disable-next-line no-var
        var UserPreferencesModel = Backbone.Model.extend({
            idAttribute: 'account_privacy',
            defaults: {
                account_privacy: 'private'
            }
        });

        return UserPreferencesModel;
    });
// eslint-disable-next-line no-undef
}).call(this, define || RequireJS.define);
