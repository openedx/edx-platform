(function(define) {
    'use strict';
    define(['jquery'], function($) {
        var edxUserCookieUtils = {
            getHostname: function() {
                return window.location.hostname;
            },

            userFromEdxUserCookie: function() {
                var hostname = this.getHostname();
                var isLocalhost = hostname.indexOf('localhost') >= 0;
                var isStage = hostname.indexOf('stage') >= 0;
                var cookie, edxUserCookie, prefix, user, userCookie;

                if (isLocalhost) {
                    // localhost doesn't have prefixes
                    edxUserCookie = 'edx-user-info';
                } else {
                    // does not take sandboxes into account
                    prefix = isStage ? 'stage' : 'prod';
                    edxUserCookie = prefix + '-edx-user-info';
                }

                cookie = document.cookie.match('(^|;)\\s*' + edxUserCookie + '\\s*=\\s*([^;]+)');
                userCookie = cookie ? cookie.pop() : $.cookie(edxUserCookie);

                // returns the user object from cookie. Replaces '054' with ',' and removes '\'
                user = userCookie.replace(/\\/g, '').replace(/054/g, ',');
                user = user.substring(1, user.length - 1);
                return JSON.parse(user);
            }
        };

        return edxUserCookieUtils;
    });
}).call(this, define || RequireJS.define);
