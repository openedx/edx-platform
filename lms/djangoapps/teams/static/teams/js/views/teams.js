(function(define) {
    'use strict';
    define([
        'backbone',
        'gettext',
        'teams/js/views/team_card',
        'common/js/components/views/paginated_view',
        'teams/js/views/team_utils'
    ], function(Backbone, gettext, TeamCardView, PaginatedView, TeamUtils) {
        var TeamsView = PaginatedView.extend({
            type: 'teams',

            srInfo: {
                id: 'heading-browse-teams',
                text: gettext('All teams')
            },

            paginationLabel: gettext('Teams Pagination'),

            initialize: function(options) {
                var view = this;
                this.context = options.context;
                this.itemViewClass = TeamCardView.extend({
                    router: options.router,
                    maxTeamSize: this.context.maxTeamSize,
                    srInfo: this.srInfo,
                    countries: TeamUtils.selectorOptionsArrayToHashWithBlank(this.context.countries),
                    languages: TeamUtils.selectorOptionsArrayToHashWithBlank(this.context.languages),
                    getTopicType: function(topicId) { return view.getTopicType(topicId); }
                });
                PaginatedView.prototype.initialize.call(this);
            },

            // eslint-disable-next-line no-unused-vars
            getTopicType: function(topicId) {
                var deferred = $.Deferred();
                deferred.resolve('open');
                return deferred.promise();
            }
        });
        return TeamsView;
    });
}).call(this, define || RequireJS.define);
