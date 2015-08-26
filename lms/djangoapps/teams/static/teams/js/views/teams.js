;(function (define) {
    'use strict';
    define([
        'backbone',
        'gettext',
        'teams/js/views/team_card',
        'common/js/components/views/paginated_view',
        'teams/js/views/team_utils'
    ], function (Backbone, gettext, TeamCardView, PaginatedView, TeamUtils) {
        var TeamsView = PaginatedView.extend({
            type: 'teams',

            srInfo: {
                id: "heading-browse-teams",
                text: gettext('All teams')
            },

            initialize: function (options) {
                this.topic = options.topic;
                this.teamMemberships = options.teamMemberships;
                this.teamParams = options.teamParams;
                this.itemViewClass = TeamCardView.extend({
                    router: options.router,
                    topic: options.topic,
                    maxTeamSize: options.maxTeamSize,
                    srInfo: this.srInfo,
                    countries: TeamUtils.selectorOptionsArrayToHashWithBlank(options.teamParams.countries),
                    languages: TeamUtils.selectorOptionsArrayToHashWithBlank(options.teamParams.languages)
                });
                PaginatedView.prototype.initialize.call(this);
            }
        });
        return TeamsView;
    });
}).call(this, define || RequireJS.define);
