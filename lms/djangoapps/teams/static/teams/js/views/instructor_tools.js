;(function (define) {
    'use strict';

    define(['backbone',
            'underscore',
            'gettext',
            'teams/js/views/team_utils',
            'common/js/components/utils/view_utils',
            'text!teams/templates/instructor-tools.underscore'],
        function (Backbone, _, gettext, TeamUtils, ViewUtils, instructorToolbarTemplate) {
            return Backbone.View.extend({

                events: {
                    'click .action-delete': 'deleteTeam',
                    'click .action-edit-members': 'editMembership'
                },

                initialize: function(options) {
                    this.template = _.template(instructorToolbarTemplate);
                    this.team = options.team;
                    this.teamEvents = options.teamEvents;
                },

                render: function() {
                    this.$el.html(this.template);
                    return this;
                },

                deleteTeam: function (event) {
                    event.preventDefault();
                    ViewUtils.confirmThenRunOperation(
                        gettext('Delete this team?'),
                        gettext('Deleting a team is permanent and cannot be undone. All members are removed from the team, and team discussions can no longer be accessed.'),
                        gettext('Delete'),
                        _.bind(this.handleDelete, this)
                    );
                },

                editMembership: function (event) {
                    event.preventDefault();
                    Backbone.history.navigate(
                        'teams/' + this.team.get('topic_id') + '/' + this.team.id +'/edit-team/manage-members',
                        {trigger: true}
                    );
                },

                handleDelete: function () {
                    var self = this,
                        postDelete = function () {
                            self.teamEvents.trigger('teams:update', {
                                action: 'delete',
                                team: self.team
                            });
                            Backbone.history.navigate('topics/' + self.team.get('topic_id'), {trigger: true});
                            TeamUtils.showMessage(
                                interpolate(
                                    gettext('Team "%(team)s" successfully deleted.'),
                                    {team: self.team.get('name')},
                                    true
                                ),
                                'success'
                            );
                        };
                    this.team.destroy().then(postDelete).fail(function (response) {
                        // In the 404 case, this team has already been
                        // deleted by someone else. Since the team was
                        // successfully deleted anyway, just show a
                        // success message.
                        if (response.status === 404) {
                            postDelete();
                        }
                    });
                }
            });
        });
}).call(this, define || RequireJS.define);
