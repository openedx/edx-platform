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
                },

                render: function() {
                    var view = this;
                    view.$el.html(view.template);
                    return view;
                },

                deleteTeam: function (event) {
                    event.preventDefault();
                    alert("You clicked the button!");
                    //placeholder; will route to delete team page
                },

                editMembership: function (event) {
                    event.preventDefault();
                    alert("You clicked the button!");
                    //placeholder; will route to remove team member page
                }
            });
        });
}).call(this, define || RequireJS.define);