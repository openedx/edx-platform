(function(define) {
    'use strict';
    define([
        'jquery',
        'backbone',
        'underscore',
        'gettext',
        'moment-with-locales',
        'js/components/card/views/card',
        'teams/js/views/team_utils',
        'edx-ui-toolkit/js/utils/html-utils',
        'text!teams/templates/team-membership-details.underscore',
        'text!teams/templates/team-country-language.underscore',
        'text!teams/templates/date.underscore'
    ], function(
        $,
        Backbone,
        _,
        gettext,
        moment,
        CardView,
        TeamUtils,
        HtmlUtils,
        teamMembershipDetailsTemplate,
        teamCountryLanguageTemplate,
        dateTemplate
    ) {
        var TeamMembershipView, TeamCountryLanguageView, TeamActivityView, TeamCardView;

        TeamMembershipView = Backbone.View.extend({
            tagName: 'div',
            className: 'team-members',
            template: HtmlUtils.template(teamMembershipDetailsTemplate),

            initialize: function(options) {
                this.maxTeamSize = options.maxTeamSize;
                this.memberships = options.memberships;
            },

            render: function() {
                var allMemberships = _(this.memberships).sortBy(function(member) {
                        return new Date(member.last_activity_at);
                    }).reverse(),
                    displayableMemberships = allMemberships.slice(0, 5),
                    maxMemberCount = this.maxTeamSize;
                HtmlUtils.setHtml(
                    this.$el,
                    this.template({
                        membership_message: TeamUtils.teamCapacityText(allMemberships.length, maxMemberCount),
                        memberships: displayableMemberships,
                        has_additional_memberships: displayableMemberships.length < allMemberships.length,
                        // Translators: "and others" refers to fact that additional members
                        // of a team exist that are not displayed.
                        sr_message: gettext('and others')
                    })
                );
                return this;
            }
        });

        TeamCountryLanguageView = Backbone.View.extend({
            template: HtmlUtils.template(teamCountryLanguageTemplate),

            initialize: function(options) {
                this.countries = options.countries;
                this.languages = options.languages;
            },

            render: function() {
                // this.$el should be the card meta div
                HtmlUtils.append(this.$el,
                    this.template({
                        country: this.countries[this.model.get('country')],
                        language: this.languages[this.model.get('language')]
                    })
                );
            }
        });

        TeamActivityView = Backbone.View.extend({
            tagName: 'div',
            className: 'team-activity',
            template: HtmlUtils.template(dateTemplate),

            initialize: function(options) {
                this.date = options.date;
            },

            render: function() {
                var lastActivity = moment(this.date),
                    currentLanguage = $('html').attr('lang');
                lastActivity.locale(currentLanguage);
                HtmlUtils.setHtml(
                    this.$el,
                    HtmlUtils.interpolateHtml(
                        // Translators: 'date' is a placeholder for a fuzzy, relative timestamp
                        // (see: http://momentjs.com/)
                        gettext('Last activity {date}'),
                        {date: this.template({date: lastActivity.format('MMMM Do YYYY, h:mm:ss a')})}
                    )
                );
                this.$('abbr').text(lastActivity.fromNow());
            }
        });

        TeamCardView = CardView.extend({
            initialize: function() {
                CardView.prototype.initialize.apply(this, arguments);
                // TODO: show last activity detail view
                this.detailViews = [
                    new TeamMembershipView({memberships: this.model.get('membership'), maxTeamSize: this.maxTeamSize}),
                    new TeamCountryLanguageView({
                        model: this.model,
                        countries: this.countries,
                        languages: this.languages
                    }),
                    new TeamActivityView({date: this.model.get('last_activity_at')})
                ];
                this.model.on('change:membership', function() {
                    this.detailViews[0].memberships = this.model.get('membership');
                }, this);
            },

            configuration: 'list_card',
            cardClass: 'team-card',
            title: function() { return this.model.get('name'); },
            description: function() { return this.model.get('description'); },
            details: function() { return this.detailViews; },
            actionClass: 'action-view',
            actionContentHtml: function() {
                return HtmlUtils.interpolateHtml(
                    gettext('View {span_start}{team_name}{span_end}'),
                    {
                        team_name: this.model.get('name'),
                        span_start: HtmlUtils.HTML('<span class="sr">'),
                        span_end: HtmlUtils.HTML('</span>')
                    }
                );
            },
            actionUrl: function() {
                return '#teams/' + this.model.get('topic_id') + '/' + this.model.get('id');
            }
        });
        return TeamCardView;
    });
}).call(this, define || RequireJS.define);
