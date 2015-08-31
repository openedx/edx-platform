;(function (define) {
    'use strict';

    define(['backbone',
            'underscore',
            'gettext',
            'teams/js/views/team_utils',
            'common/js/components/views/feedback_prompt',
            'text!teams/templates/instructor-tools.underscore'],
        function (Backbone, _, gettext, TeamUtils, PromptView, instructorToolbarTemplate) {
            return Backbone.View.extend({

                events: {
                    'click .action-delete': 'deleteTeam',
                    'click .action-edit-members': 'editMembership'
                },

                initialize: function(options) {
                    this.template = _.template(instructorToolbarTemplate);
                    this.team = options.team;
                    this.teamEvents = options.teamEvents;
                    this.router = options.router;
                },

                render: function() {
                    this.$el.html(this.template);
                    return this;
                },

                deleteTeam: function (event) {
                    event.preventDefault();
                    var self = this;
                    var msg = new PromptView.Warning({
                        title: gettext('Delete this team?'),
                        message: gettext('Deleting a team removes it from the team listing view, and removes members from the team as well.'),
                        actions: {
                            primary: {
                                text: gettext('Delete'),
                                class: 'action-delete',
                                click: function () {
                                    msg.hide();
                                    self.handleDelete();
                                }
                            },
                            secondary: {
                                text: gettext('Close'),
                                class: 'action-cancel',
                                click: function () {
                                    msg.hide();
                                }
                            }
                        }
                    });
                    msg.show()
                },

                editMembership: function (event) {
                    event.preventDefault();
                    alert("You clicked the button!");
                    //placeholder; will route to remove team member page
                },

                handleDelete: function () {
                    var self = this;
                    this.team.destroy().then(function () {
                        self.teamEvents.trigger('teams:update', {
                            action: 'delete',
                            team: self.team
                        });
                        self.router.navigate('topics/' + self.team.get('topic_id'), {trigger: true});
                    });
                }
            });
        });
}).call(this, define || RequireJS.define);
