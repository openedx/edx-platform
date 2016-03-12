/**
 * View for an individual team.
 */
(function(define) {
    'use strict';
    define(
        [
            'backbone',
            'underscore',
            'gettext',
            'edx-ui-toolkit/js/utils/html-utils',
            'common/js/components/utils/view_utils',
            'teams/js/views/team_utils',
            'teams/js/views/team_discussion',
            'text!teams/templates/team-profile.underscore',
            'text!teams/templates/team-member.underscore'
        ],
        function(Backbone, _, gettext, HtmlUtils, ViewUtils, TeamUtils, TeamDiscussionView,
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
                    this.discussionView = new TeamDiscussionView({
                        el: this.$('.discussion-module')
                    });
                    this.discussionView.render();

                    this.renderTeamMembers();

                    this.setFocusToHeaderFunc();
                    return this;
                },

                renderTeamMembers: function() {
                    var view = this;
                    _.each(this.model.get('membership'), function(membership) {
                        HtmlUtils.append(
                            view.$('.members-info'),
                            HtmlUtils.template(teamMemberTemplate)({
                                imageUrl: membership.user.profile_image.image_url_medium,
                                username: membership.user.username,
                                memberProfileUrl: '/u/' + membership.user.username
                            })
                        );
                    });
                },

                selectText: function(event) {
                    event.preventDefault();
                    $(event.currentTarget).select();
                },

                leaveTeam: function(event) {
                    var view = this;
                    event.preventDefault();
                    ViewUtils.confirmThenRunOperation(
                        gettext('Leave this team?'),
                        gettext("If you leave, you can no longer post in this team's discussions. Your place will be available to another learner."),  // eslint-disable-line max-len
                        gettext('Confirm'),
                        function() {
                            $.ajax({
                                type: 'DELETE',
                                url: view.context.teamMembershipDetailUrl.replace('team_id', view.model.get('id'))
                            }).done(function() {
                                view.model.fetch()
                                    .done(function() {
                                        view.teamEvents.trigger('teams:update', {
                                            action: 'leave',
                                            team: view.model
                                        });
                                    });
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
