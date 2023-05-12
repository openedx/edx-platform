/**
 * Utility methods for emitting teams events. See the event spec:
 * https://openedx.atlassian.net/wiki/display/AN/Teams+Feature+Event+Design
 */
(function(define) {
    'use strict';

    define([
        'logger'
    ], function(Logger) {
        // eslint-disable-next-line no-var
        var TeamAnalytics = {
            emitPageViewed: function(pageName, topicId, teamId) {
                Logger.log('edx.team.page_viewed', {
                    page_name: pageName,
                    topic_id: topicId,
                    team_id: teamId
                });
            }
        };

        return TeamAnalytics;
    });
// eslint-disable-next-line no-undef
}).call(this, define || RequireJS.define);
