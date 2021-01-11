(function(define) {
    'use strict';
    define([
        'jquery',
        'backbone',
        'underscore',
        'gettext',
        'moment',
        'js/components/card/views/card',
        'teams/js/views/team_utils',
        'text!teams/templates/team-membership-details.underscore',
        'text!teams/templates/team-country-language.underscore',
        'text!teams/templates/date.underscore',
        'edx-ui-toolkit/js/utils/html-utils',
        'edx-ui-toolkit/js/utils/string-utils'
    ], function(
        $,
        Backbone,
        _,
        gettext,
        moment,
        CardView,
        TeamUtils,
        teamMembershipDetailsTemplate,
        teamCountryLanguageTemplate,
        dateTemplate,
        HtmlUtils,
        StringUtils
    ) {
        var TeamMembershipView, TeamCountryLanguageView, TeamActivityView, TeamCardView;

        TeamMembershipView = Backbone.View.extend({
            tagName: 'div',
            className: 'team-members',

            initialize: function(options) {
                this.getTopic = options.getTopic;
                this.topicId = options.topicId;
                this.courseMaxTeamSize = options.courseMaxTeamSize;
                this.memberships = options.memberships;
            },

            render: function() {
                var view = this;
                this.getTopic(this.topicId).done(function(topic) {
                    view.renderMessage(topic.getMaxTeamSize(view.courseMaxTeamSize));
                }).fail(function() {
                    view.renderMessage(view.courseMaxTeamSize);
                });
                return view;
            },

            renderMessage: function(maxTeamSize) {
                var allMemberships = _(this.memberships).sortBy(function(member) {
                        return new Date(member.last_activity_at);
                    }).reverse(),
                    displayableMemberships = allMemberships.slice(0, 5);
                HtmlUtils.setHtml(
                    this.$el,
                    HtmlUtils.template(teamMembershipDetailsTemplate)({
                        membership_message: TeamUtils.teamCapacityText(allMemberships.length, maxTeamSize),
                        memberships: displayableMemberships,
                        has_additional_memberships: displayableMemberships.length < allMemberships.length,
                        /* Translators: "and others" refers to fact that additional
                         * members of a team exist that are not displayed. */
                        sr_message: gettext('and others')
                    })
                );
            }
        });

        TeamCountryLanguageView = Backbone.View.extend({
            initialize: function(options) {
                this.countries = options.countries;
                this.languages = options.languages;
            },

            render: function() {
                // this.$el should be the card meta div
                HtmlUtils.append(
                    this.$el,
                    HtmlUtils.template(teamCountryLanguageTemplate)({
                        country: this.countries[this.model.get('country')],
                        language: this.languages[this.model.get('language')]
                    })
                );
            }
        });

        TeamActivityView = Backbone.View.extend({
            tagName: 'div',
            className: 'team-activity',
            template: _.template(dateTemplate),

            initialize: function(options) {
                this.date = options.date;
            },

            render: function() {
                var lastActivity = moment(this.date),
                    currentLanguage = $('html').attr('lang');
                lastActivity.locale(currentLanguage);
                HtmlUtils.setHtml(
                    this.$el,
                    HtmlUtils.HTML(
                        StringUtils.interpolate(
                            /* Translators: 'date' is a placeholder for a fuzzy,
                             * relative timestamp (see: http://momentjs.com/)
                             */
                            gettext('Last activity {date}'),
                            {date: this.template({date: lastActivity.format('MMMM Do YYYY, h:mm:ss a')})},
                            true
                        )
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
                    new TeamMembershipView({
                        memberships: this.model.get('membership'),
                        courseMaxTeamSize: this.courseMaxTeamSize,
                        topicId: this.model.get('topic_id'),
                        getTopic: this.getTopic
                    }),
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

                this.teamsetName = null;
                this.getTopic(this.model.get('topic_id')).done(_.bind(function(teamset) {
                    this.teamsetName = teamset.get('name');
                }, this));
            },

            configuration: 'list_card',
            cardClass: 'team-card',
            title: function() { return this.model.get('name'); },
            pennant: function() { return this.showTeamset ? this.teamsetName : undefined; },
            description: function() { return this.model.get('description'); },
            details: function() { return this.detailViews; },
            actionClass: 'action-view',
            actionContent: function() {
                return StringUtils.interpolate(
                    gettext('View {span_start} {team_name} {span_end}'),
                    {span_start: '<span class="sr">', team_name: _.escape(this.model.get('name')), span_end: '</span>'},
                    true
                );
            },
            actionUrl: function() {
                return '#teams/' + this.model.get('topic_id') + '/' + this.model.get('id');
            },
            // eslint-disable-next-line no-unused-vars
            getTopic: function(topicId) {
                // This function will be overrwritten in the extended class
                // that will in turn be overwritten by functions in TopicTeamsView and MyTeamsView
                return null;
            }
        });
        return TeamCardView;
    });
}).call(this, define || RequireJS.define);
