(function(define) {
    'use strict';
    define([
        'underscore',
        'backbone',
        'gettext',
        'edx-ui-toolkit/js/utils/html-utils',
        'teams/js/views/teams',
        'common/js/components/views/paging_header',
        'text!teams/templates/team-actions.underscore',
        'teams/js/views/team_utils'
    ], function(_, Backbone, gettext, HtmlUtils, TeamsView, PagingHeader, teamActionsTemplate, TeamUtils) {
        // Translators: this string is shown at the bottom of the teams page
        // to find a team to join or else to create a new one. There are three
        // links that need to be included in the message:
        // 1. Browse teams in other topics
        // 2. search teams
        // 3. create a new team
        // Be careful to start each link with the appropriate start indicator
        // (e.g. {browse_span_start} for #1) and finish it with {span_end}.
        const actionsMessage = interpolate_text( // eslint-disable-line no-undef
            _.escape(
                gettext(
                    '{browse_span_start}Browse teams in other ' +
                    'topics{span_end} or {search_span_start}search teams{span_end} ' +
                    'in this topic. If you still can\'t find a team to join, ' +
                    '{create_span_start}create a new team in this topic{span_end}.'
                )
            ),
            {
                browse_span_start: '<a class="browse-teams" href="">',
                search_span_start: '<a class="search-teams" href="">',
                create_span_start: '<a class="create-team" href="">',
                span_end: '</a>'
            }
        );

        const TopicTeamsView = TeamsView.extend({
            events: {
                'click a.browse-teams': 'browseTeams',
                'click a.search-teams': 'searchTeams',
                'click a.create-team': 'showCreateTeamForm'
            },

            initialize: function(options) {
                this.options = _.extend({}, options);
                this.showSortControls = options.showSortControls;
                this.context = options.context;
                TeamsView.prototype.initialize.call(this, options);
            },

            /**
             * Send an AJAX query checking on whether the user is in a team in the given
             * teamset.
             * If the response comes back with a failure, do not show actions.
             */
            checkIfOnTeamInTeamset: async function() {
                return new Promise((resolve) => {
                    $.ajax({
                        type: 'GET',
                        url: this.context.teamMembershipsUrl,
                        data: {
                            username: this.context.userInfo.username,
                            course_id: this.context.courseID,
                            teamset_id: this.model.get('id'),
                        }
                    }).done(
                        data => resolve(data.count === 0)
                    ).fail(
                        //TODO: should we throw an exception here?
                        () => resolve(false)
                    );
                });
            },

            /**
             * Append the actionsMessage string to the element into the `message` key in the django template.
             */
            drawActions: function() {
                HtmlUtils.append(
                    this.$el,
                    HtmlUtils.template(teamActionsTemplate)({ message: actionsMessage })
                );
            },


            /**
             * Try to render the actions message.
             * Show actions if student is staff/priviledged or if the team is not instructor-managed and
             * the student is not on a team in the teamset.
             */
            tryRenderActions: function() {
                //
                const { staff, priviledged } = this.context.userInfo;
                if (staff || priviledged) {
                    return this.drawActions();
                }
                if (TeamUtils.isInstructorManagedTopic(this.model.attributes.type)) {
                    return null;
                }
                return this.checkIfOnTeamInTeamset().then(
                    onTeamInTeamset => !onTeamInTeamset && this.drawActions()
                );
            },

            render: function() {
                this.collection.refresh().done(() => {
                    TeamsView.prototype.render.call(this);
                    this.tryRenderActions();
                });
            },

            browseTeams: function(event) {
                event.preventDefault();
                Backbone.history.navigate('browse', {trigger: true});
            },

            searchTeams: function(event) {
                var $searchField = $('.page-header-search .search-field');
                event.preventDefault();
                $searchField.focus();
                $searchField.select();
                $('html, body').animate({ scrollTop: 0 }, 500);
            },

            showCreateTeamForm: function(event) {
                event.preventDefault();
                Backbone.history.navigate(
                    'topics/' + this.model.id + '/create-team',
                    { trigger: true }
                );
            },

            createHeaderView: function() {
                return new PagingHeader({
                    collection: this.options.collection,
                    srInfo: this.srInfo,
                    showSortControls: this.showSortControls
                });
            },

            getTopic: function(topicId) { // eslint-disable-line no-unused-vars
                var deferred = $.Deferred();
                deferred.resolve(this.model);
                return deferred.promise();
            }
        });

        return TopicTeamsView;
    });
}).call(this, define || RequireJS.define);
