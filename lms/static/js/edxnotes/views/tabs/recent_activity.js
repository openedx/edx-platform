;(function (define, undefined) {
'use strict';
define([
    'gettext', 'js/edxnotes/views/tab_panel', 'js/edxnotes/views/tab_view'
], function (gettext, TabPanelView, TabView) {
    var view = 'Recent Activity';
    var RecentActivityView = TabView.extend({
        PanelConstructor: TabPanelView.extend({
            id: 'recent-panel',
            title: view,
            className: function () {
                return [
                    TabPanelView.prototype.className,
                    'note-group'
                ].join(' ');
            },
            renderContent: function () {
                this.$el.append(this.getNotes(this.collection.toArray()));
                return this;
            }
        }),

        tabInfo: {
            identifier: 'view-recent-activity',
            name: gettext('Recent Activity'),
            icon: 'fa fa-clock-o',
            view: view
        }
    });

    return RecentActivityView;
});
}).call(this, define || RequireJS.define);
