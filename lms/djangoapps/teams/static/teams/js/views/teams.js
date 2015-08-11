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
                this.topic = options.topic;
                this.itemViewClass = TeamCardView.extend({
                    router: options.router,
                    topic: options.topic,
                    maxTeamSize: options.maxTeamSize,
                    countries: this.selectorOptionsArrayToHashWithBlank(options.teamParams.countries),
                    languages: this.selectorOptionsArrayToHashWithBlank(options.teamParams.languages),
                });
                PaginatedView.prototype.initialize.call(this);
                this.teamParams = options.teamParams;
                this.showActions = options.showActions;
            },

            render: function () {
                PaginatedView.prototype.render.call(this);

                if (this.showActions === true) {
                    var teamActionsView = new TeamActionsView({
                        teamParams: this.teamParams
                    });
                    this.$el.append(teamActionsView.$el);
                    teamActionsView.render();
                }

                return this;
            },

            /**
             * Convert a 2d array to an object equivalent with an additional blank element
             *
             * @param {Array.<Array.<string>>} Two dimensional options array
             * @returns {Object} Hash version of the input array
             * @example selectorOptionsArrayToHashWithBlank([["a", "alpha"],["b","beta"]])
             * // returns {"a":"alpha", "b":"beta", "":""}
             */
            selectorOptionsArrayToHashWithBlank: function (options) {
                var map = _.object(options);
                map[""] = "";
                return map;
            }
        });
        return TeamsView;
    });
}).call(this, define || RequireJS.define);
