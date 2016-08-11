(function(define) {
    'use strict';
    define([
        'gettext',
        'teams/js/views/topic_card',
        'teams/js/views/team_utils',
        'common/js/components/views/paging_header',
        'common/js/components/views/paginated_view'
    ], function(gettext, TopicCardView, TeamUtils, PagingHeader, PaginatedView) {
        var TopicsView = PaginatedView.extend({
            type: 'topics',

            srInfo: {
                id: 'heading-browse-topics',
                text: gettext('All topics')
            },

            initialize: function(options) {
                this.options = _.extend({}, options);
                this.itemViewClass = TopicCardView.extend({
                    router: options.router,
                    srInfo: this.srInfo
                });
                PaginatedView.prototype.initialize.call(this);
            },

            createHeaderView: function() {
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
                        TeamUtils.hideMessage();
                    });
                return this;
            }
        });
        return TopicsView;
    });
}).call(this, define || RequireJS.define);
