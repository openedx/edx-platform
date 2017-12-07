/**
 *  Store data for the current entitlement.
 */
(function(define) {
    'use strict';

    define([
        'backbone'
    ],
        function(Backbone) {
            return Backbone.Model.extend({
                defaults: {
                    availableSessions: [],
                    entitlementUUID: '',
                    currentSessionId: '',
                    courseName: '',
                    expiredAt: null,
                    daysUntilExpiration: Number.MAX_VALUE
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
