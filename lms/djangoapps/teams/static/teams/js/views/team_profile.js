/**
 * View for an individual team.
 */
;(function (define) {
    'use strict';
    define(['backbone', 'underscore', 'gettext', 'teams/js/views/team_discussion',
            'teams/js/views/team_utils',
            'text!teams/templates/team-profile.underscore',
            'text!teams/templates/team-member.underscore'],
        function (Backbone, _, gettext, TeamDiscussionView, TeamUtils, teamTemplate, teamMemberTemplate) {
            var TeamProfileView = Backbone.View.extend({

                errorMessage: gettext("An error occurred. Try again."),

                events: {
                    'click .invite-link-input': 'selectText',
                    'click .leave-team-link': 'leaveTeam'
                },
                initialize: function (options) {
                    this.listenTo(this.model, "change", this.render);
                    this.courseID = options.courseID;
                    this.maxTeamSize = options.maxTeamSize;
                    this.requestUsername = options.requestUsername;
                    this.isPrivileged = options.isPrivileged;
                    this.teamInviteUrl = options.teamInviteUrl;
                    this.teamMembershipDetailUrl = options.teamMembershipDetailUrl;

                    this.countries = TeamUtils.selectorOptionsArrayToHashWithBlank(options.countries);
                    this.languages = TeamUtils.selectorOptionsArrayToHashWithBlank(options.languages);

                },

                render: function () {
                    var memberships = this.model.get('membership'),
                        discussionTopicID = this.model.get('discussion_topic_id'),
                        isMember = TeamUtils.isUserMemberOfTeam(memberships, this.requestUsername);

                    this.$el.html(_.template(teamTemplate, {
                        courseID: this.courseID,
                        discussionTopicID: discussionTopicID,
                        readOnly: !(this.isPrivileged || isMember),
                        country: this.countries[this.model.get('country')],
                        language: this.languages[this.model.get('language')],
                        membershipText: TeamUtils.teamCapacityText(memberships.length, this.maxTeamSize),
                        isMember: isMember,
                        hasCapacity: memberships.length < this.maxTeamSize,
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
                    _.each(this.model.get('membership'), function(membership) {
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
                },

                leaveTeam: function (event) {
                    event.preventDefault();
                    var view = this;
                    $.ajax({
                       type: 'DELETE',
                       url: view.teamMembershipDetailUrl.replace('team_id', view.model.get('id'))
                    }).done(function (data) {
                       view.model.fetch({});
                    }).fail(function (data) {
                        TeamUtils.parseAndShowMessage(data, view.errorMessage);
                    });
                }
            });

            return TeamProfileView;
        });
}).call(this, define || RequireJS.define);
