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
                this.context = options.context;
                this.itemViewClass = TeamCardView.extend({
                    router: options.router,
                    maxTeamSize: this.context.maxTeamSize,
                    srInfo: this.srInfo,
                    // TODO: Move below 2 line out as we are changing edx default files
                    roomID: this.context.roomID,
                    nodeBBUrl: this.context.nodeBBUrl,
                    countries: TeamUtils.selectorOptionsArrayToHashWithBlank(this.context.countries),
                    languages: TeamUtils.selectorOptionsArrayToHashWithBlank(this.context.languages)
                });
                PaginatedView.prototype.initialize.call(this);
            }
        });
        return TeamsView;
    });
}).call(this, define || RequireJS.define);
