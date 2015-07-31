/**
 * View for an individual team.
 */
;(function (define) {
    'use strict';
    define(['backbone', 'underscore', 'gettext', 'teams/js/views/team_discussion',
            'teams/js/views/team_utils',
            'text!teams/templates/team-profile.underscore',
            'text!teams/templates/team-member.underscore'
        ],
        function (Backbone, _, gettext, TeamDiscussionView, TeamUtils, teamTemplate, teamMemberTemplate) {
            var TeamProfileView = Backbone.View.extend({

                events: {
                    'click .invite-link-input': 'selectText'
                },
                initialize: function (options) {
                    this.courseID = options.courseID;
                    this.discussionTopicID = this.model.get('discussion_topic_id');
                    this.maxTeamSize = options.maxTeamSize;
                    this.memberships = this.model.get('membership');
                    this.readOnly = options.readOnly;
                    this.requestUsername = options.requestUsername;
                    this.teamInviteUrl = options.teamInviteUrl;

                    this.countries = TeamUtils.selectorOptionsArrayToHashWithBlank(options.countries);
                    this.languages = TeamUtils.selectorOptionsArrayToHashWithBlank(options.languages);

                },

                render: function () {
                    this.$el.html(_.template(teamTemplate, {
                        courseID: this.courseID,
                        discussionTopicID: this.discussionTopicID,
                        readOnly: this.readOnly,
                        country: this.countries[this.model.get('country')],
                        language: this.languages[this.model.get('language')],
                        membershipText: TeamUtils.teamCapacityText(this.memberships.length, this.maxTeamSize),
                        isMember: TeamUtils.isUserMemberOfTeam(this.memberships, this.requestUsername),
                        hasCapacity: this.memberships.length < this.maxTeamSize,
                        inviteLink: this.teamInviteUrl

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
                    _.each(this.memberships, function(membership) {
                        view.$('.members-info').append(_.template(teamMemberTemplate, {
                            imageUrl: membership.user.profile_image.image_url_medium,
                            username: membership.user.username,
                            memberProfileUrl: '/u/' + membership.user.username
                        }));
                    });
                },

                selectText: function(event) {
                    event.preventDefault();
                    $(event.currentTarget).select();
                }
            });

            return TeamProfileView;
        });
}).call(this, define || RequireJS.define);
