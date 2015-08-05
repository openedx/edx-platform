;(function (define) {
    'use strict';
    define([
        'gettext',
        'underscore',
        'backbone',
        'text!teams/templates/team-actions.underscore'
    ], function (gettext, _, Backbone, team_actions_template) {
        return Backbone.View.extend({
            events: {
                'click a.browse-teams': 'browseTeams',
                'click a.search-team-descriptions': 'searchTeamDescriptions',
                'click a.create-team': 'showCreateTeamForm'
            },

            initialize: function (options) {
                this.template = _.template(team_actions_template);
                this.teamParams = options.teamParams;
            },

            render: function () {
                var message = interpolate_text(
                    _.escape(gettext("Try {browse_span_start}browsing all teams{span_end} or {search_span_start}searching team descriptions{span_end}. If you still can't find a team to join, {create_span_start}create a new team in this topic{span_end}.")),
                    {
                        'browse_span_start': '<a class="browse-teams" href="">',
                        'search_span_start': '<a class="search-team-descriptions" href="">',
                        'create_span_start': '<a class="create-team" href="">',
                        'span_end': '</a>'
                    }
                );
                this.$el.html(this.template({message: message}));
                return this;
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
                Backbone.history.navigate('topics/' + this.teamParams.topicId + '/create-team', {trigger: true});
            }
        });
    });
}).call(this, define || RequireJS.define);
