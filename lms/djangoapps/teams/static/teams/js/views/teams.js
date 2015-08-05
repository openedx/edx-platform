;(function (define) {
    'use strict';
    define([
        'backbone',
        'teams/js/views/team_card',
        'common/js/components/views/paginated_view',
        'teams/js/views/team_actions'
    ], function (Backbone, TeamCardView, PaginatedView, TeamActionsView) {
        var TeamsView = PaginatedView.extend({
            type: 'teams',

            initialize: function (options) {
                this.itemViewClass = TeamCardView.extend({
                    router: options.router,
                    maxTeamSize: options.maxTeamSize
                });
                PaginatedView.prototype.initialize.call(this);
                this.teamParams = options.teamParams;
            },

            render: function () {
                PaginatedView.prototype.render.call(this);

                var teamActionsView = new TeamActionsView({
                    teamParams: this.teamParams
                });
                this.$el.append(teamActionsView.$el);
                teamActionsView.render();
                return this;
            }
        });
        return TeamsView;
    });
}).call(this, define || RequireJS.define);
