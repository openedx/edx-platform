;(function (define) {
    'use strict';
    define([
        'backbone',
        'gettext',
        'teams/js/views/team_card',
        'common/js/components/views/paginated_view'
    ], function (Backbone, gettext, TeamCardView, PaginatedView) {
        var TeamsView = PaginatedView.extend({
            type: 'teams',

            events: {
                'click button.action': '' // entry point for team creation
            },

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
                    countries: this.selectorOptionsArrayToHashWithBlank(options.teamParams.countries),
                    languages: this.selectorOptionsArrayToHashWithBlank(options.teamParams.languages),
                    srInfo: this.srInfo
                });
                PaginatedView.prototype.initialize.call(this);
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
