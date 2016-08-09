/**
 * Model for a team membership.
 */
(function(define) {
    'use strict';
    define(['backbone', 'teams/js/models/team'], function(Backbone, TeamModel) {
        var TeamMembership = Backbone.Model.extend({
            defaults: {
                date_joined: '',
                last_activity_at: '',
                team: null,
                user: null
            },

            parse: function(response) {
                response.team = new TeamModel(response.team);
                return response;
            }
        });
        return TeamMembership;
    });
}).call(this, define || RequireJS.define);
