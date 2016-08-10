/**
 * Utility methods for emitting teams events. See the event spec:
 * https://openedx.atlassian.net/wiki/display/AN/Teams+Feature+Event+Design
 */
(function(define) {
    'use strict';

    define([
        'logger'
    ], function(Logger) {
        var TeamAnalytics = {
            emitPageViewed: function(page_name, topic_id, team_id) {
                Logger.log('edx.team.page_viewed', {
                    page_name: page_name,
                    topic_id: topic_id,
                    team_id: team_id
                });
            }
        };

        return TeamAnalytics;
    });
}).call(this, define || RequireJS.define);
