/*  Team utility methods*/
;(function (define) {
    'use strict';
    define([
    ], function () {
        return {

            /**
             * Convert a 2d array to an object equivalent with an additional blank element
             *
             * @param options {Array.<Array.<string>>} Two dimensional options array
             * @returns {Object} Hash version of the input array
             * @example selectorOptionsArrayToHashWithBlank([["a", "alpha"],["b","beta"]])
             * // returns {"a":"alpha", "b":"beta", "":""}
             */
            selectorOptionsArrayToHashWithBlank: function (options) {
                var map = _.object(options);
                map[""] = "";
                return map;
            },

            teamCapacityText: function (memberCount, maxMemberCount) {
                return interpolate(
                    // Translators: The following message displays the number of members on a team.
                    ngettext(
                        '%(memberCount)s / %(maxMemberCount)s Member',
                        '%(memberCount)s / %(maxMemberCount)s Members',
                        maxMemberCount
                    ),
                    {memberCount: memberCount, maxMemberCount: maxMemberCount}, true
                )
            },
            isUserMemberOfTeam: function(memberships, requestUsername) {
                return _.isObject(
                    _.find(memberships, function(membership)
                    {
                        return membership.user.username === requestUsername;
                    })
                );
            }
        }
    });

}).call(this, define || RequireJS.define);
