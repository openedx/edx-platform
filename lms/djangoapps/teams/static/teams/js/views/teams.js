;(function (define) {
    'use strict';
    define([
        'backbone',
        'teams/js/views/team_card',
        'common/js/components/views/paginated_view',
        'text!teams/templates/team-actions.underscore'
    ], function (Backbone, TeamCardView, PaginatedView, teamActionsTemplate) {
        var TeamsView = PaginatedView.extend({
            type: 'teams',

            events: {
                'click a.browse-teams': 'browseTeams',
                'click a.search-team-descriptions': 'searchTeamDescriptions',
                'click a.create-team': 'showCreateTeamForm'
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
                    languages: this.selectorOptionsArrayToHashWithBlank(options.teamParams.languages)
                });
                PaginatedView.prototype.initialize.call(this);
            },

            render: function () {
                PaginatedView.prototype.render.call(this);

                if (this.teamMemberships.canUserCreateTeam()) {
                    var message = interpolate_text(
                        _.escape(gettext("Try {browse_span_start}browsing all teams{span_end} or {search_span_start}searching team descriptions{span_end}. If you still can't find a team to join, {create_span_start}create a new team in this topic{span_end}.")),
                        {
                            'browse_span_start': '<a class="browse-teams" href="">',
                            'search_span_start': '<a class="search-team-descriptions" href="">',
                            'create_span_start': '<a class="create-team" href="">',
                            'span_end': '</a>'
                        }
                    );
                    this.$el.append(_.template(teamActionsTemplate, {message: message}));
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
            },

            browseTeams: function (event) {
                event.preventDefault();
                Backbone.history.navigate('browse', {trigger: true});
            },

            searchTeamDescriptions: function (event) {
                event.preventDefault();
                // TODO! Will navigate to correct place once required functionality is available
                Backbone.history.navigate('browse', {trigger: true});
            },

            showCreateTeamForm: function (event) {
                event.preventDefault();
                Backbone.history.navigate('topics/' + this.teamParams.topicID + '/create-team', {trigger: true});
            }
        });
        return TeamsView;
    });
}).call(this, define || RequireJS.define);
