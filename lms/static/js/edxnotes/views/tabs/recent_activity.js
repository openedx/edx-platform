;(function (define, undefined) {
'use strict';
define([
    'gettext', 'underscore',  'backbone', 'js/edxnotes/views/note_item',
    'js/edxnotes/views/tab_view', 'underscore.string'
], function (gettext, _, Backbone, NoteItemView, TabView) {
    var RecentActivityView = TabView.extend({
        SubViewConstructor: Backbone.View.extend({
            tagName: 'section',
            className: 'tab-panel',
            id: 'recent-panel',
            render: function () {
                var container = document.createDocumentFragment();
                container.appendChild(this.getTitle());
                this.collection.each(function (model) {
                    var item = new NoteItemView({model: model});
                    container.appendChild(item.render().el);
                });
                this.$el.html(container);
                return this;
            },

            getTitle: function () {
                return $('<h2></h2>', {
                    'class': 'sr',
                    'text': gettext('Recent Activity')
                }).get(0);
            }
        }),

        tabInfo: {
            identifier: 'view-recent-activity',
            name: gettext('Recent Activity'),
            icon: 'icon-time'
        }
    });

    return RecentActivityView;
});
}).call(this, define || RequireJS.define);
