;(function (define) {
    'use strict';

    define(['backbone',
            'underscore',
            'gettext',
            'teams/js/models/team',
            'common/js/components/views/feedback_prompt',
            'text!teams/templates/edit-team-member.underscore',
            'text!teams/templates/date.underscore'
    ],
        function (Backbone, _, gettext, TeamModel, PromptView, editTeamMemberTemplate, dateTemplate) {
            return Backbone.View.extend({
                dateTemplate: _.template(dateTemplate),
                teamMemberTemplate: _.template(editTeamMemberTemplate),

                events: {
                    'click .action-remove-member': 'removeMember'
                },

                initialize: function(options) {
                    this.teamMembershipDetailUrl = options.teamMembershipDetailUrl.replace('team_id', this.model.get('id'));
                    this.teamMembershipDetailUrl = this.teamMembershipDetailUrl.replace(options.requestUsername, '');
                    this.teamEvents = options.teamEvents;
                },

                render: function() {
                    this.$el.html('<ul class="edit-members"></ul>');
                    this.renderTeamMembers();
                },

                renderTeamMembers: function() {
                    var self = this, dateJoined, lastActivity;

                    _.each(this.model.get('membership'), function(membership) {
                        dateJoined = interpolate(
                            // Translators: 'date' is a placeholder for a fuzzy, relative timestamp (see: https://github.com/rmm5t/jquery-timeago)
                            gettext("Joined %(date)s"),
                            {date: self.dateTemplate({date: membership.date_joined})},
                            true
                        );

                        lastActivity = interpolate(
                            // Translators: 'date' is a placeholder for a fuzzy, relative timestamp (see: https://github.com/rmm5t/jquery-timeago)
                            gettext("Last Activity %(date)s"),
                            {date: self.dateTemplate({date: membership.last_activity_at})},
                            true
                        );

                        // I don't think I need to sort these because they will automatically be in
                        // the order in which they joined the team.
                        self.$('.edit-members').append(self.teamMemberTemplate({
                            imageUrl: membership.user.profile_image.image_url_medium,
                            username: membership.user.username,
                            memberProfileUrl: '/u/' + membership.user.username,
                            dateJoined: dateJoined,
                            lastActive: lastActivity
                        }));
                    });
                    this.$('abbr').timeago();
                },

                removeMember: function (event) {
                    var self = this, username = $(event.currentTarget).data('username');
                    event.preventDefault();

                    var msg = new PromptView.Warning({
                        title: gettext('Remove this team member?'),
                        message: gettext('The member will be permanently removed from the team, allowing another user to take the available spot.'),
                        actions: {
                            primary: {
                                text: gettext('Delete'),
                                class: 'action-delete',
                                click: function () {
                                    msg.hide();
                                    $.ajax({
                                        type: 'DELETE',
                                        url: self.teamMembershipDetailUrl + username
                                    }).done(function (data) {
                                        debugger
//                                        self.model.fetch()
//                                            .done(function() {
//                                                view.teamEvents.trigger('teams:update', {
//                                                    action: 'leave',
//                                                    team: view.model
//                                                });
//                                            });
                                    }).fail(function (data) {
                                        // TeamUtils.parseAndShowMessage(data, view.errorMessage);
                                    });
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
                    msg.show();
                }
            });
        });
}).call(this, define || RequireJS.define);
