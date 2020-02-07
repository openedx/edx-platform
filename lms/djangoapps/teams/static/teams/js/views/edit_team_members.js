(function(define) {
    'use strict';

    define(['backbone',
        'jquery',
        'underscore',
        'gettext',
        'teams/js/models/team',
        'teams/js/views/team_utils',
        'common/js/components/utils/view_utils',
        'text!teams/templates/edit-team-member.underscore',
        'text!teams/templates/date.underscore'
    ],
        function(
            Backbone, $, _, gettext, TeamModel, TeamUtils, ViewUtils, editTeamMemberTemplate, dateTemplate) {
            return Backbone.View.extend({
                dateTemplate: _.template(dateTemplate),
                teamMemberTemplate: _.template(editTeamMemberTemplate),
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
                        this.$el.html( // xss-lint: disable=javascript-jquery-html
                          // eslint-disable-next-line max-len
                          '<p>' + gettext('This team does not have any members.') + '</p>'); // xss-lint: disable=javascript-concat-html
                    } else {
                        this.$el.html('<ul class="edit-members"></ul>'); // xss-lint: disable=javascript-jquery-html
                        this.renderTeamMembers();
                    }
                    return this;
                },

                renderTeamMembers: function() {
                    var self = this,
                        dateJoined, lastActivity;

                    _.each(this.model.get('membership'), function(membership) {
                        // eslint-disable-next-line no-undef
                        dateJoined = interpolate(
                            /* Translators: 'date' is a placeholder for a fuzzy,
                             * relative timestamp (see: https://github.com/rmm5t/jquery-timeago)
                             */
                            gettext('Joined %(date)s'),
                            {date: self.dateTemplate({date: membership.date_joined})},
                            true
                        );

                        // eslint-disable-next-line no-undef
                        lastActivity = interpolate(
                            /* Translators: 'date' is a placeholder for a fuzzy,
                             * relative timestamp (see: https://github.com/rmm5t/jquery-timeago)
                             */
                            gettext('Last Activity %(date)s'),
                            {date: self.dateTemplate({date: membership.last_activity_at})},
                            true
                        );

                        // It is assumed that the team member array is automatically in the order of date joined.
                        // eslint-disable-next-line max-len
                        self.$('.edit-members').append(self.teamMemberTemplate({ // xss-lint: disable=javascript-jquery-append
                            imageUrl: membership.user.profile_image.image_url_medium,
                            username: membership.user.username,
                            memberProfileUrl: '/u/' + membership.user.username,
                            dateJoined: dateJoined,
                            lastActive: lastActivity
                        }));
                    });
                    this.$('abbr').timeago();
                },

                removeMember: function(event) {
                    var self = this,
                        username = $(event.currentTarget).data('username');
                    event.preventDefault();

                    ViewUtils.confirmThenRunOperation(
                        gettext('Remove this team member?'),
                        gettext('This learner will be removed from the team,' +
                            'allowing another learner to take the available spot.'),
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
