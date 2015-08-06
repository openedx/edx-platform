/**
 * View for an individual team.
 */
;(function (define) {
    'use strict';
    define(['backbone', 'underscore', 'gettext', 'teams/js/views/team_discussion',
            'text!teams/templates/team-profile.underscore',
            'text!teams/templates/team-member.underscore'
        ],
        function (Backbone, _, gettext, TeamDiscussionView, teamTemplate, teamMemberTemplate) {
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

                    this.country = this.model.get('country');
                    this.language = this.model.get('language');

                    // TODO un comment this when country and language PR merge in
                    //this.country = options.countries[this.model.get('country')];
                    //this.language = options.languages[this.model.get('language')];
                },

                render: function () {
                    this.$el.html(_.template(teamTemplate, {
                        courseID: this.courseID,
                        discussionTopicID: this.discussionTopicID,
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
                            {member_count: this.memberships.length, max_member_count: this.maxTeamSize}, true
                        ),
                        isMember: this.isUserMemberOfTeam(),
                        hasCapacity: this.memberships.length < this.maxTeamSize,
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
                    _.each(this.memberships, function(membership) {
                        view.$('.members-info').append(_.template(teamMemberTemplate, {
                            imageUrl: 'https://dkxj5n08iyd6q.cloudfront.net/54.208.48.207/759220e8c562e167cab003f0023f839e_50.jpg?v=1438793481',
                            username: membership.user.id,
                            memberProfileUrl: '/u/' + membership.user.id
                        }));
                    });
                },
                isUserMemberOfTeam: function() {
                    var view = this;
                    var member = _.find(this.memberships, function (membership) {
                        return membership.user.id === view.requestUsername
                    });
                    return member ? true : false;
                },
                selectText: function(event) {
                    event.preventDefault();
                    $(event.currentTarget).select();
                }
            });

            return TeamProfileView;
        });
}).call(this, define || RequireJS.define);
