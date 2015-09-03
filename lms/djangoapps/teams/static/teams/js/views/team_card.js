;(function (define) {
    'use strict';
    define([
        'backbone',
        'underscore',
        'gettext',
        'jquery.timeago',
        'js/components/card/views/card',
        'teams/js/views/team_utils',
        'text!teams/templates/team-membership-details.underscore',
        'text!teams/templates/team-country-language.underscore',
        'text!teams/templates/team-activity.underscore'
    ], function (
        Backbone,
        _,
        gettext,
        timeago,
        CardView,
        TeamUtils,
        teamMembershipDetailsTemplate,
        teamCountryLanguageTemplate,
        teamActivityTemplate
    ) {
        var TeamMembershipView, TeamCountryLanguageView, TeamActivityView, TeamCardView;

        TeamMembershipView = Backbone.View.extend({
            tagName: 'div',
            className: 'team-members',
            template: _.template(teamMembershipDetailsTemplate),

            initialize: function (options) {
                this.maxTeamSize = options.maxTeamSize;
            },

            render: function () {
                var allMemberships = _(this.model.get('membership'))
                        .sortBy(function (member) {return new Date(member.last_activity_at);}).reverse(),
                    displayableMemberships = allMemberships.slice(0, 5),
                    maxMemberCount = this.maxTeamSize;
                this.$el.html(this.template({
                    membership_message: TeamUtils.teamCapacityText(allMemberships.length, maxMemberCount),
                    memberships: displayableMemberships,
                    has_additional_memberships: displayableMemberships.length < allMemberships.length,
                    // Translators: "and others" refers to fact that additional members of a team exist that are not displayed.
                    sr_message: gettext('and others')
                }));
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

        TeamActivityView = Backbone.View.extend({
            tagName: 'div',
            className: 'team-activity',
            template: _.template(teamActivityTemplate),

            initialize: function (options) {
                this.date = options.date;
            },

            render: function () {
                this.$el.html(
                    interpolate(
                        // Translators: 'date' is a placeholder for a fuzzy, relative timestamp (see: https://github.com/rmm5t/jquery-timeago)
                        gettext("Last Activity %(date)s"),
                        {date: this.template({date: this.date})},
                        true
                    )
                );
                this.$('abbr').timeago();
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
                    }),
                    new TeamActivityView({date: this.teamModel().get('last_activity_at')})
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
