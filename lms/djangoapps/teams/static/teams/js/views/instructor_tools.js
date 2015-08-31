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
                    'click .action-delete': 'deleteTeam',
                    'click .action-edit-members': 'editMembership'
                },

                initialize: function(options) {
                    this.template = _.template(instructorToolbarTemplate);
                    this.teamEvents = options.teamEvents;
                    this.team = options.team;
                },

                render: function() {
                    this.$el.html(this.template);
                    return this;
                },

                deleteTeam: function (event) {
                    event.preventDefault();
                    alert("You clicked the button!");
                    //placeholder; will route to delete team page
                },

                editMembership: function (event) {
                    event.preventDefault();
                    Backbone.history.navigate(
                        'topics/' + this.team.get('topic_id') + '/' + this.team.id +'/edit-team/manage-members',
                        {trigger: true}
                    );
                }
            });
        });
}).call(this, define || RequireJS.define);
