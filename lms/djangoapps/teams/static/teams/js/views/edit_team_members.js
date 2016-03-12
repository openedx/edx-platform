(function(define) {
    'use strict';

    define(['backbone',
            'jquery',
            'underscore',
            'gettext',
            'edx-ui-toolkit/js/utils/html-utils',
            'edx-ui-toolkit/js/utils/string-utils',
            'common/js/components/utils/view_utils',
            'teams/js/views/team_utils',
            'teams/js/models/team',
            'text!teams/templates/edit-team-member.underscore',
            'text!teams/templates/date.underscore'
    ],
        function(Backbone, $, _, gettext, HtmlUtils, StringUtils, ViewUtils, TeamUtils, TeamModel,
                 editTeamMemberTemplate, dateTemplate) {
            return Backbone.View.extend({
                dateTemplate: HtmlUtils.template(dateTemplate),
                teamMemberTemplate: HtmlUtils.template(editTeamMemberTemplate),
                errorMessage: gettext('An error occurred while removing the member from the team. Try again.'),

                events: {
                    'click .action-remove-member': 'removeMember'
                },

                initialize: function(options) {
                    this.options = _.extend({}, options);
                    // The URL ends with team_id,request_username. We want to replace
                    // the last occurrence of team_id with the actual team_id, and remove request_username
                    // as the actual user to be removed from the team will be added on before calling DELETE.
                    this.teamMembershipDetailUrl = options.context.teamMembershipDetailUrl.substring(
                        0, this.options.context.teamMembershipDetailUrl.lastIndexOf('team_id')
                    ) + this.model.get('id') + ',';

                    this.teamEvents = options.teamEvents;
                },

                render: function() {
                    if (this.model.get('membership').length === 0) {
                        HtmlUtils.setHtml(
                            this.$el,
                            HtmlUtils.joinHtml(
                                HtmlUtils.HTML('<p>'),
                                gettext('This team does not have any members.'),
                                HtmlUtils.HTML('</p>')
                            )
                        );
                    } else {
                        HtmlUtils.setHtml(this.$el, HtmlUtils.HTML('<ul class="edit-members"></ul>'));
                        this.renderTeamMembers();
                    }
                    return this;
                },

                renderTeamMembers: function() {
                    var self = this,
                        dateJoinedHtml, lastActivityHtml;

                    _.each(this.model.get('membership'), function(membership) {
                        dateJoinedHtml = HtmlUtils.interpolateHtml(
                            // Translators: 'date' is a placeholder for a fuzzy, relative timestamp
                            // (see: https://github.com/rmm5t/jquery-timeago)
                            gettext('Joined {date}'),
                            {date: self.dateTemplate({date: membership.date_joined})}
                        );

                        lastActivityHtml = HtmlUtils.interpolateHtml(
                            // Translators: 'date' is a placeholder for a fuzzy, relative timestamp
                            // (see: https://github.com/rmm5t/jquery-timeago)
                            gettext('Last Activity {date}'),
                            {date: self.dateTemplate({date: membership.last_activity_at})}
                        );

                        // It is assumed that the team member array is automatically in the order of date joined.
                        HtmlUtils.append(
                            self.$('.edit-members'),
                            self.teamMemberTemplate({
                                imageUrl: membership.user.profile_image.image_url_medium,
                                imageUrlAlt: StringUtils.interpolate(
                                    "{username}'s profile page",  // jshint ignore:line
                                    {username: membership.user.username}
                                ),
                                username: membership.user.username,
                                memberProfileUrl: '/u/' + membership.user.username,
                                dateJoinedHtml: dateJoinedHtml,
                                lastActivityHtml: lastActivityHtml
                            })
                        );
                    });
                    this.$('abbr').timeago();
                },

                removeMember: function(event) {
                    var self = this,
                        username = $(event.currentTarget).data('username');
                    event.preventDefault();

                    ViewUtils.confirmThenRunOperation(
                        gettext('Remove this team member?'),
                        gettext('This learner will be removed from the team, allowing another learner to take the available spot.'),  // eslint-disable-line max-len
                        gettext('Remove'),
                        function() {
                            $.ajax({
                                type: 'DELETE',
                                url: self.teamMembershipDetailUrl.concat(username, '?admin=true')
                            }).done(function() {
                                self.teamEvents.trigger('teams:update', {
                                    action: 'leave',
                                    team: self.model
                                });
                                self.model.fetch().done(function() { self.render(); });
                            }).fail(function(data) {
                                TeamUtils.parseAndShowMessage(data, self.errorMessage);
                            });
                        }
                    );
                }
            });
        });
}).call(this, define || RequireJS.define);
