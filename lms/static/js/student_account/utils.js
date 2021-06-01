(function(define) {
    'use strict';
    define(['jquery'], function($) {
        var userFromEdxUserCookie = function() {
            var hostname = window.location.hostname;
            var isLocalhost = hostname.indexOf('localhost') >= 0;
            var isStage = hostname.indexOf('stage') >= 0;
            var edxUserCookie, prefix, user;

            if (isLocalhost) {
                // localhost doesn't have prefixes
                edxUserCookie = 'edx-user-info';
            } else {
                // does not take sandboxes into account
                prefix = isStage ? 'stage' : 'prod';
                edxUserCookie = prefix + '-edx-user-info';
            }
            // returns the user object from cookie. Replaces '054' with ',' and removes '\'
            user = $.cookie(edxUserCookie).replace(/\\/g, '').replace(/054/g, ',');
            user = user.substring(1, user.length - 1);
            return JSON.parse(user);
        };

        return {
            userFromEdxUserCookie: userFromEdxUserCookie
        };
    });
}).call(this, define || RequireJS.define);
