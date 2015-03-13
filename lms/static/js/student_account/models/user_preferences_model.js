;(function (define, undefined) {
    'use strict';
    define([
        'gettext', 'underscore', 'backbone',
    ], function (gettext, _, Backbone) {

        var UserPreferencesModel = Backbone.Model.extend({
            idAttribute: 'account_privacy',
            defaults: {
                account_privacy: 'private'
            }
        });

        return UserPreferencesModel;
    })
}).call(this, define || RequireJS.define);