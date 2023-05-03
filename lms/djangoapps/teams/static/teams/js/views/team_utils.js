/*  Team utility methods*/
(function(define) {
    'use strict';
    define(['jquery', 'underscore', 'edx-ui-toolkit/js/utils/string-utils'],
        function($, _, StringUtils) {
            return {

                /**
             * Convert a 2d array to an object equivalent with an additional blank element
             *
             * @param options {Array.<Array.<string>>} Two dimensional options array
             * @returns {Object} Hash version of the input array
             * @example selectorOptionsArrayToHashWithBlank([["a", "alpha"],["b","beta"]])
             * // returns {"a":"alpha", "b":"beta", "":""}
             */
                selectorOptionsArrayToHashWithBlank: function(options) {
                    var map = _.object(options);
                    map[''] = '';
                    return map;
                },

                teamCapacityText: function(memberCount, maxMemberCount) {
                    var formatString;
                    var parameters = {memberCount: memberCount};
                    if (maxMemberCount === null) {
                        formatString = '{memberCount}';
                    } else {
                        formatString = '{memberCount} / {maxMemberCount}';
                        parameters.maxMemberCount = maxMemberCount;
                    }
                    return StringUtils.interpolate(
                    // Translators: The following message displays the number of members on a team.
                        ngettext(
                            formatString + ' Member',
                            formatString + ' Members',
                            maxMemberCount || memberCount
                        ),
                        parameters, true
                    );
                },

                isUserMemberOfTeam: function(memberships, requestUsername) {
                    return _.isObject(
                        _.find(memberships, function(membership) {
                            return membership.user.username === requestUsername;
                        })
                    );
                },

                hideMessage: function() {
                    $('#teams-message').addClass('.is-hidden');
                },

                showMessage: function(message, type) {
                    var $messageElement = $('#teams-message');
                    if (_.isUndefined(type)) {
                        type = 'warning'; // eslint-disable-line no-param-reassign
                    }
                    $messageElement.removeClass('is-hidden').addClass(type);
                    $('.teams-content .msg-content .copy').text(message);
                    $messageElement.focus();
                },

                /**
             * Parse `data` and show user message. If parsing fails than show `genericErrorMessage`
             */
                parseAndShowMessage: function(data, genericErrorMessage, type) {
                    try {
                        var errors = JSON.parse(data.responseText); // eslint-disable-line vars-on-top
                        this.showMessage(
                            _.isUndefined(errors.user_message) ? genericErrorMessage : errors.user_message, type
                        );
                    } catch (error) {
                        this.showMessage(genericErrorMessage, type);
                    }
                },

                isInstructorManagedTopic: function(topicType) {
                    if (topicType === undefined) {
                        return false;
                    }
                    return topicType.toLowerCase() !== 'open';
                },

                /** Shows info/error banner for team membership CSV upload
             * @param: content - string or array for display
             * @param: isError - true sets error styling, false/none uses info styling
             */
                showInfoBanner: function(content, isError) {
                // clear message
                    var $message = $('#team-management-assign .page-banner .message-content');
                    $message.html('');

                    // set message
                    if (Array.isArray(content)) {
                        content.forEach(function(item) {
                        // xss-lint: disable=javascript-jquery-append
                            $message.append($('<p>').text(item));
                        });
                    } else {
                        $('#team-management-assign .page-banner .message-content').text(content);
                    }

                    // set color sytling
                    $('#team-management-assign .page-banner .alert')
                        .toggleClass('alert-success', !isError)
                        .toggleClass('alert-danger', isError);

                    // set icon styling
                    $('#team-management-assign .page-banner .icon')
                        .toggleClass('fa-check', !isError)
                        .toggleClass('fa-warning', isError);

                    $('#team-management-assign .page-banner').show();
                }
            };
        });
}).call(this, define || RequireJS.define);
