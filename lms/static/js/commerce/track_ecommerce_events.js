/**
 *
 * A library of helper functions to track ecommerce related events.
 *
 */
(function(define) {
    'use strict';
    define([], function() {
        var trackUpsellClick = function(linkElement, linkName, optionalAttrs) {
            var eventAttrs = {linkName: linkName};
            var allowedAttrs = ['linkType', 'pageName', 'linkCategory'];
            if (!window.analytics) {
                return;
            }

            if (
                typeof optionalAttrs !== 'undefined' &&
                optionalAttrs !== null &&
                Object.keys(optionalAttrs).length > 0
            ) {
                allowedAttrs.forEach(function(allowedAttr) {
                    eventAttrs[allowedAttr] = optionalAttrs[allowedAttr];
                });
            }

            console.log('eventAttrs', eventAttrs);
            console.log('allowedAttrs', allowedAttrs);
        };

        var TrackECommerceEvents = {trackUpsellClick: trackUpsellClick};

        return TrackECommerceEvents;
    });
}).call(this, define || RequireJS.define);
