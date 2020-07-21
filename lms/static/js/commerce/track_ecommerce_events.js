/**
 *
 * A library of helper functions to track ecommerce related events.
 *
 */
(function(define) {
    'use strict';
    define([], function() {
        var trackUpsellClick = function(elt, linkName, optionalAttrs) {
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

            window.analytics.trackLink(elt, 'edx.bi.ecommerce.upsell_links_clicked', eventAttrs);
        };

        var TrackECommerceEvents = {trackUpsellClick: trackUpsellClick};

        return TrackECommerceEvents;
    });
}).call(this,
    typeof define === 'function' && define.amd ? define : RequireJS.define
);
