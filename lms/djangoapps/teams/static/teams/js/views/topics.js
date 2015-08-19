;(function (define) {
    'use strict';
    define([
        'gettext',
        'teams/js/views/topic_card',
        'common/js/components/views/paginated_view'
    ], function (gettext, TopicCardView, PaginatedView) {
        var TopicsView = PaginatedView.extend({
            type: 'topics',

            srInfo: {
                id: "heading-browse-topics",
                text: gettext("All topics")
            },

            initialize: function (options) {
                this.itemViewClass = TopicCardView.extend({
                    router: options.router,
                    srInfo: this.srInfo
                });
                PaginatedView.prototype.initialize.call(this);
            },

            render: function() {
                var self = this;
                this.collection.refresh()
                    .done(function() {
                        self.collection.isStale = false;
                        PaginatedView.prototype.render.call(self);
                    });
                return this;
            }
        });
        return TopicsView;
    });
}).call(this, define || RequireJS.define);
