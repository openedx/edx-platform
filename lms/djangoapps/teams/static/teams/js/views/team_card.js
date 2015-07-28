;(function (define) {
    'use strict';
    define([
        'backbone',
        'underscore',
        'gettext',
        'js/components/card/views/card',
        'text!teams/templates/team-country-language.underscore'
    ], function (Backbone, _, gettext, CardView, teamCountryLanguageTemplate) {
        var TeamMembershipView, TeamCountryLanguageView, TeamCardView;

        TeamMembershipView = Backbone.View.extend({
            tagName: 'div',
            className: 'team-members',
            template: _.template(
                '<span class="member-count"><%= membership_message %></span>' +
                '<ul class="list-member-thumbs"></ul>'
            ),

            initialize: function (options) {
                this.maxTeamSize = options.maxTeamSize;
            },

            render: function () {
                var memberships = this.model.get('membership'),
                    maxMemberCount = this.maxTeamSize;
                this.$el.html(this.template({
                    membership_message: interpolate(
                        // Translators: The following message displays the number of members on a team.
                        ngettext(
                            '%(member_count)s / %(max_member_count)s Member',
                            '%(member_count)s / %(max_member_count)s Members',
                            maxMemberCount
                        ),
                        {member_count: memberships.length, max_member_count: maxMemberCount}, true
                    )
                }));
                _.each(memberships, function (membership) {
                    this.$('list-member-thumbs').append(
                        '<li class="item-member-thumb"><img alt="' + membership.user.username + '" src=""></img></li>'
                    );
                }, this);
                return this;
            }
        });

        TeamCountryLanguageView = Backbone.View.extend({
            template: _.template(teamCountryLanguageTemplate),

            render: function() {
                // this.$el should be the card meta div
                this.$el.append(this.template({
                    country: this.model.get('country'),
                    language: this.model.get('language')
                }));
            }
        });

        TeamCardView = CardView.extend({
            initialize: function () {
                CardView.prototype.initialize.apply(this, arguments);
                // TODO: show last activity detail view
                this.detailViews = [
                    new TeamMembershipView({model: this.model, maxTeamSize: this.maxTeamSize}),
                    new TeamCountryLanguageView({model: this.model})
                ];
            },

            configuration: 'list_card',
            cardClass: 'team-card',
            title: function () { return this.model.get('name'); },
            description: function () { return this.model.get('description'); },
            details: function () { return this.detailViews; },
            actionClass: 'action-view',
            actionContent: function() {
                return interpolate(
                    gettext('View %(span_start)s %(team_name)s %(span_end)s'),
                    {span_start: '<span class="sr">', team_name: this.model.get('name'), span_end: '</span>'},
                    true
                );
            },
            action: function (event) {
                var url = 'teams/' + this.topic.get('id') + '/' + this.model.get('id');
                event.preventDefault();
                this.router.navigate(url, {trigger: true});
            }
        });
        return TeamCardView;
    });
}).call(this, define || RequireJS.define);
