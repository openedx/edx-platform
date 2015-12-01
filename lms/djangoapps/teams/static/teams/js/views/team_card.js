;(function (define) {
    'use strict';
    define([
        'backbone',
        'underscore',
        'gettext',
        'js/components/card/views/card',
        'teams/js/views/team_utils',
        'text!teams/templates/team-country-language.underscore'
    ], function (Backbone, _, gettext, CardView, TeamUtils, teamCountryLanguageTemplate) {
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
                    membership_message: TeamUtils.teamCapacityText(memberships.length, maxMemberCount)
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

            initialize: function (options) {
                this.countries = options.countries;
                this.languages = options.languages;
            },

            render: function() {
                // this.$el should be the card meta div
                this.$el.append(this.template({
                    country: this.countries[this.model.get('country')],
                    language: this.languages[this.model.get('language')]
                }));
            }
        });

        TeamCardView = CardView.extend({
            initialize: function () {
                CardView.prototype.initialize.apply(this, arguments);
                // TODO: show last activity detail view
                this.detailViews = [
                    new TeamMembershipView({model: this.teamModel(), maxTeamSize: this.maxTeamSize}),
                    new TeamCountryLanguageView({
                        model: this.teamModel(),
                        countries: this.countries,
                        languages: this.languages
                    })
                ];
            },

            teamModel: function () {
                if (this.model.has('team')) { return this.model.get('team'); };
                return this.model;
            },

            configuration: 'list_card',
            cardClass: 'team-card',
            title: function () { return this.teamModel().get('name'); },
            description: function () { return this.teamModel().get('description'); },
            details: function () { return this.detailViews; },
            actionClass: 'action-view',
            actionContent: function() {
                return interpolate(
                    gettext('View %(span_start)s %(team_name)s %(span_end)s'),
                    {span_start: '<span class="sr">', team_name: this.teamModel().get('name'), span_end: '</span>'},
                    true
                );
            },
            actionUrl: function () {
                return '#teams/' + this.teamModel().get('topic_id') + '/' + this.teamModel().get('id');
            }
        });
        return TeamCardView;
    });
}).call(this, define || RequireJS.define);
