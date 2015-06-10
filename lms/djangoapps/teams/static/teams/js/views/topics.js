;(function (define) {
    'use strict';
    define([
        'backbone',
        'underscore',
        'common/js/components/views/list',
        'common/js/components/views/paging_header',
        'common/js/components/views/paging_footer',
        'teams/js/views/topic_card'
    ], function (Backbone, _, ListView, PagingHeaderView, PagingFooterView, TopicCardView) {
        var TopicsListView = ListView.extend({
            itemViewClass: TopicCardView
        });

        var TopicsView = Backbone.View.extend({
            initialize: function() {
                this.listView = new TopicsListView({collection: this.collection, tagName: 'ol'});
            },

            render: function() {
                this.$el.append(this.listView.render().el);
            }
        });
        return TopicsView;
    });
}).call(this, define || RequireJS.define);
