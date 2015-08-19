/**
 * Model for a team membership.
 */
(function (define) {
    'use strict';
    define(['backbone', 'teams/js/models/team'], function (Backbone, TeamModel) {
        var TeamMembership = Backbone.Model.extend({
            defaults: {
                date_joined: '',
                team: null,
                user: null
            },

            parse: function (response, options) {
                response.team = new TeamModel(response.team);
                return response;
            }
        });
        return TeamMembership;
    });
}).call(this, define || RequireJS.define);
