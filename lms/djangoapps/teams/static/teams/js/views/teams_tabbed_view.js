/**
 * A custom TabbedView for Teams.
 */
(function(define) {
    'use strict';

    define([
        'common/js/components/views/tabbed_view',
        'teams/js/utils/team_analytics'
    ], function(TabbedView, TeamAnalytics) {
        var TeamsTabbedView = TabbedView.extend({
            /**
             * Overrides TabbedView.prototype.setActiveTab in order to
             * log page viewed events.
             */
            setActiveTab: function(index) {
                TabbedView.prototype.setActiveTab.call(this, index);
                TeamAnalytics.emitPageViewed(this.getTabMeta(index).tab.url, null, null);
            }
        });

        return TeamsTabbedView;
    });
}).call(this, define || RequireJS.define);
