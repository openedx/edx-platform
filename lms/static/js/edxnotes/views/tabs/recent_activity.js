;(function (define, undefined) {
'use strict';
define([
    'gettext', 'js/edxnotes/views/subview', 'js/edxnotes/views/tab_view'
], function (gettext, SubView, TabView) {
    var RecentActivityView = TabView.extend({
        SubViewConstructor: SubView.extend({
            id: 'edx-notes-page-recent-activity',
            templateName: 'recent-activity-item',
            render: function () {
                this.$el.html(this.template({collection: this.collection}));

                return this;
            }
        }),

        tabInfo: {
            name: gettext('Recent Activity'),
            class_name: 'tab-recent-activity'
        }
    });

    return RecentActivityView;
});
}).call(this, define || RequireJS.define);
