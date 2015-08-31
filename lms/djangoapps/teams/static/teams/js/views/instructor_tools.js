;(function (define) {
    'use strict';

    define(['backbone',
            'underscore',
            'gettext',
            'teams/js/views/team_utils',
            'text!teams/templates/instructor-tools.underscore'],
        function (Backbone, _, gettext, TeamUtils, instructorToolbarTemplate) {
            return Backbone.View.extend({

                events: {
                    'click .action-delete': 'deleteTeamClicked',
                    'click .action-edit-members': 'editTeamMembersClicked'
                },

                initialize: function(options) {
                    this.template = _.template(instructorToolbarTemplate);
                    this.teamEvents = options.teamEvents;
                    this.team = options.team;
                    this.topic = options.topic;
                    this.router = options.router;
                    this.editTeamMembers = options.editTeamMembers;
                },

                render: function() {
                    this.$el.html(this.template);
                    return this;
                },

                deleteTeamClicked: function (event) {
                    event.preventDefault();
                    alert("You clicked the button!");
                    //placeholder; will route to delete team page
                },

                editTeamMembersClicked: function (event) {
                    event.preventDefault();
                    this.editTeamMembers(this.topic, this.team);
                }
            });
        });
}).call(this, define || RequireJS.define);
