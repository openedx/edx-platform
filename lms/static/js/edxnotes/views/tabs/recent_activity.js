;(function (define, undefined) {
'use strict';
define([
    'gettext', 'js/edxnotes/views/tab_panel', 'js/edxnotes/views/tab_view'
], function (gettext, TabPanelView, TabView) {
    var RecentActivityView = TabView.extend({
        SubViewConstructor: TabPanelView.extend({
            id: 'recent-panel',
            title: 'Recent Activity',
            renderContent: function () {
                this.$el.append(this.getNotes(this.collection.toArray()));
                return this;
            }
        }),

        tabInfo: {
            identifier: 'view-recent-activity',
            name: gettext('Recent Activity'),
            icon: 'icon-clock-o'
        }
    });

    return RecentActivityView;
});
}).call(this, define || RequireJS.define);
