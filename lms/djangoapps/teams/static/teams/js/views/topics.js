;(function (define) {
    'use strict';
    define([
        'teams/js/views/topic_card',
        'common/js/components/views/paginated_view'
    ], function (TopicCardView, PaginatedView) {
        var TopicsView = PaginatedView.extend({
            type: 'topics',

            initialize: function (options) {
                this.itemViewClass = TopicCardView.extend({router: options.router});
                PaginatedView.prototype.initialize.call(this);
            }
        });
        return TopicsView;
    });
}).call(this, define || RequireJS.define);
