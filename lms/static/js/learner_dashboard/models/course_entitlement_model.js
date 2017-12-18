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
                    courseName: ''
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
