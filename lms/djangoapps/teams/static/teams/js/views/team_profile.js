/**
 * View for an individual team.
 */
(function(define) {
    'use strict';
    define([
        'jquery',
        'backbone',
        'underscore',
        'gettext',
        'edx-ui-toolkit/js/utils/html-utils',
        'teams/js/views/team_discussion',
        'common/js/components/utils/view_utils',
        'teams/js/views/team_utils',
        'text!teams/templates/team-profile.underscore',
        'text!teams/templates/team-member.underscore'
    ],
        function($, Backbone, _, gettext, HtmlUtils, TeamDiscussionView, ViewUtils, TeamUtils,
                  teamTemplate, teamMemberTemplate) {
            var TeamProfileView = Backbone.View.extend({

                errorMessage: gettext('An error occurred. Try again.'),

                events: {
                    'click .leave-team-link': 'leaveTeam'
                },

                initialize: function(options) {
                    this.teamEvents = options.teamEvents;
                    this.context = options.context;
                    this.setFocusToHeaderFunc = options.setFocusToHeaderFunc;

                    this.countries = TeamUtils.selectorOptionsArrayToHashWithBlank(this.context.countries);
                    this.languages = TeamUtils.selectorOptionsArrayToHashWithBlank(this.context.languages);

                    this.listenTo(this.model, 'change', this.render);
                },

                render: function() {
                    var memberships = this.model.get('membership'),
                        discussionTopicID = this.model.get('discussion_topic_id'),
                        isMember = TeamUtils.isUserMemberOfTeam(memberships, this.context.userInfo.username);

                    HtmlUtils.setHtml(
                        this.$el,
                        HtmlUtils.template(teamTemplate)({
                            courseID: this.context.courseID,
                            discussionTopicID: discussionTopicID,
                            readOnly: !(this.context.userInfo.privileged || isMember),
                            country: this.countries[this.model.get('country')],
                            language: this.languages[this.model.get('language')],
                            membershipText: TeamUtils.teamCapacityText(memberships.length, this.context.maxTeamSize),
                            isMember: isMember,
                            hasCapacity: memberships.length < this.context.maxTeamSize,
                            hasMembers: memberships.length >= 1
                        })
                    );

                    this.renderTeamMembers();

                    // TODO: WRITE THE FOLLOWING CODE USING PROPER BACKBONE LOGIC
                    var nodeBBUrl = localStorage.getItem('nodebbUrl');
                    var rooms = JSON.parse(localStorage.getItem('rooms'));
                    var activeTeam = localStorage.getItem('activeTeam')
                    var memberships = parseInt(localStorage.getItem('memberships'), 10);
                    var teamDiscussionLink = nodeBBUrl + '/chats/' + rooms[activeTeam];
                    var discussionLinkElem = document.getElementById('discussion-link');

                    discussionLinkElem.href = 'javascript:void(0)';
                    if (!rooms[activeTeam]) {
                        discussionLinkElem.innerHTML = '';
                    } else if (rooms[activeTeam] && memberships <= 1) {
                        discussionLinkElem.innerHTML = '<h3>Not enough members to start a discussion</h3>'
                    } else {
                        discussionLinkElem.href = teamDiscussionLink;
                    }

                    this.setFocusToHeaderFunc();
                    return this;
                },

                renderTeamMembers: function() {
                    var view = this;
                    _.each(this.model.get('membership'), function(membership) {
                        $.post({
                            url: '/philu/api/profile/data',
                            data: {
                                username: membership.user.username
                            },
                            success: function(data) {
                                HtmlUtils.append(
                                    view.$('.members-info'),
                                    HtmlUtils.template(teamMemberTemplate)({
                                        imageUrl: data.payload.picture !== "" ?
                                            data.payload.picture :
                                            membership.user.profile_image.image_url_medium,
                                        username: membership.user.username,
                                        memberProfileUrl: data.payload.profileUrl
                                    })
                                );
                            },
                            error: function(err) {
                                console.error("Error: " + err)
                            }
                        });
                    });
                },

                selectText: function(event) {
                    event.preventDefault();
                    $(event.currentTarget).select();
                },

                leaveTeam: function(event) {
                    event.preventDefault();
                    var view = this;
                    ViewUtils.confirmThenRunOperation(
                        gettext('Leave this team?'),
                        gettext("If you leave, you can no longer post in this team's discussions. Your place will be available to another learner."),
                        gettext('Confirm'),
                        function() {
                            $.ajax({
                                type: 'DELETE',
                                url: view.context.teamMembershipDetailUrl.replace('team_id', view.model.get('id'))
                            }).done(function(data) {
                                view.model.fetch()
                                    .done(function() {
                                        view.teamEvents.trigger('teams:update', {
                                            action: 'leave',
                                            team: view.model
                                        });
                                    });
                                window.location = ".";
                            }).fail(function(data) {
                                TeamUtils.parseAndShowMessage(data, view.errorMessage);
                            });
                        }
                    );
                }
            });

            return TeamProfileView;
        });
}).call(this, define || RequireJS.define);
