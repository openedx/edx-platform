/**
 * View for an individual team.
 */
;(function (define) {
    'use strict';
    define(['backbone', 'underscore', 'gettext', 'teams/js/views/team_discussion',
            "common/js/components/views/feedback_prompt",
            'text!teams/templates/team-profile.underscore',
            'text!teams/templates/team-member.underscore'
        ],
        function (Backbone, _, gettext, TeamDiscussionView, PromptView, teamTemplate, teamMemberTemplate) {
            var TeamProfileView = Backbone.View.extend({

                events: {
                    'click .invite-link-input': 'selectText',
                    'click .leave-team-link': 'leaveTeam'
                },
                initialize: function (options) {
                    this.listenTo(this.model, "change", this.render);
                    this.courseID = options.courseID;
                    this.maxTeamSize = options.maxTeamSize;
                    this.readOnly = options.readOnly;
                    this.requestUsername = options.requestUsername;

                    this.country = this.model.get('country');
                    this.language = this.model.get('language');

                    // TODO un comment this when country and language PR merge in
                    //this.country = options.countries[this.model.get('country')];
                    //this.language = options.languages[this.model.get('language')];

                    this.teamsMembershipDetailUrl = options.teamsMembershipDetailUrl;
                    _.bindAll(this, 'leaveTeam', 'confirmThenRunOperation');
                },

                render: function () {
                    var memberships = this.model.get('membership');
                    var discussionTopicID = this.model.get('discussion_topic_id');
                    this.$el.html(_.template(teamTemplate, {
                        courseID: this.courseID,
                        discussionTopicID: discussionTopicID,
                        readOnly: this.readOnly,
                        country: this.country,
                        language: this.language,
                        membershipText: interpolate(
                            // Translators: The following message displays the number of members on a team.
                            ngettext(
                                '%(member_count)s / %(max_member_count)s Member',
                                '%(member_count)s / %(max_member_count)s Members',
                                this.maxTeamSize
                            ),
                            {member_count: memberships.length, max_member_count: this.maxTeamSize}, true
                        ),
                        isMember: this.isUserMemberOfTeam(),
                        hasCapacity: memberships.length < this.maxTeamSize,
                        inviteLink: window.location +'?invite=true'

                    }));
                    this.discussionView = new TeamDiscussionView({
                        el: this.$('.discussion-module')
                    });
                    this.discussionView.render();

                    this.renderTeamMembers();
                    return this;
                },

                renderTeamMembers: function() {
                    var view = this;
                    _.each(this.model.get('membership'), function(membership) {
                        view.$('.members-info').append(_.template(teamMemberTemplate, {
                            imageUrl: 'https://dkxj5n08iyd6q.cloudfront.net/54.208.48.207/759220e8c562e167cab003f0023f839e_50.jpg?v=1438793481',
                            username: membership.user.username,
                            memberProfileUrl: '/u/' + membership.user.username
                        }));
                    });
                },
                isUserMemberOfTeam: function() {
                    var view = this;
                    var member = _.find(this.model.get('membership'), function (membership) {
                        return membership.user.username === view.requestUsername
                    });
                    return member ? true : false;
                },
                selectText: function(event) {
                    event.preventDefault();
                    $(event.currentTarget).select();
                },

                /**
                 * Confirms with the user whether to run an operation or not, and then runs it if desired.
                 */
                confirmThenRunOperation: function(title, message, actionLabel, operation, onCancelCallback) {
                    return new PromptView.Warning({
                        title: title,
                        message: message,
                        actions: {
                            primary: {
                                text: actionLabel,
                                click: function(prompt) {
                                    prompt.hide();
                                    operation();
                                }
                            },
                            secondary: {
                                text: gettext('Cancel'),
                                click: function(prompt) {
                                    if (onCancelCallback) {
                                        onCancelCallback();
                                    }
                                    return prompt.hide();
                                }
                            }
                        }
                    }).show();
                },

                leaveTeam: function (event) {
                    event.preventDefault();
                    var view = this;
                    this.confirmThenRunOperation(
                        gettext('Leave this team?'),
                        gettext('Leaving a team means you can no longer post on this team, and your spot is opened for another learner.'),
                        gettext('Leave'),
                        function() {
                            $.ajax({
                               type: 'DELETE',
                               url: view.teamsMembershipDetailUrl.replace('team_id', view.model.get('id'))
                            }).done(function (data) {
                               view.model.fetch({});
                            }).fail(function (data) {
                               alert(data);
                            });
                            console.log('Left the team!');
                        }
                    );
                }
            });

            return TeamProfileView;
        });
}).call(this, define || RequireJS.define);
