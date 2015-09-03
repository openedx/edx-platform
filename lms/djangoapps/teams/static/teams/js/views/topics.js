;(function (define) {
    'use strict';
    define([
        'gettext',
        'teams/js/views/topic_card',
        'common/js/components/views/paging_header',
        'common/js/components/views/paginated_view'
    ], function (gettext, TopicCardView, PagingHeader, PaginatedView) {
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

            createHeaderView: function () {
                return new PagingHeader({
                    collection: this.options.collection,
                    srInfo: this.srInfo,
                    showSortControls: true
                });
            },

            render: function() {
                var self = this;
                this.collection.refresh()
                    .done(function() {
                        PaginatedView.prototype.render.call(self);
                    });
                return this;
            }
        });
        return TopicsView;
    });
}).call(this, define || RequireJS.define);
