(function(define) {
    'use strict';
    define([
        'jquery',
        'underscore',
        'backbone',
        'gettext',
        'edx-ui-toolkit/js/utils/html-utils',
        'teams/js/views/teams',
        'common/js/components/views/paging_header',
        'text!teams/templates/team-actions.underscore',
        'teams/js/views/team_utils'
    ], function($, _, Backbone, gettext, HtmlUtils, TeamsView, PagingHeader, teamActionsTemplate, TeamUtils) {
        // Translators: this string is shown at the bottom of the teams page
        // to find a team to join or else to create a new one. There are three
        // links that need to be included in the message:
        // 1. Browse teams in other topics
        // 2. search teams
        // 3. create a new team
        // Be careful to start each link with the appropriate start indicator
        // (e.g. {browse_span_start} for #1) and finish it with {span_end}.
        var actionMessage = interpolate_text(  // eslint-disable-line no-undef
            _.escape(gettext(
                '{browse_span_start}Browse teams in other ' +
                'topics{span_end} or {search_span_start}search teams{span_end} ' +
                'in this topic. If you still can\'t find a team to join, ' +
                '{create_span_start}create a new team in this topic{span_end}.'
            )),
            {
                browse_span_start: '<a class="browse-teams" href="">',
                search_span_start: '<a class="search-teams" href="">',
                create_span_start: '<a class="create-team" href="">',
                span_end: '</a>'
            }
        );

        var canUserCreateTeamErrorMessage = gettext(
            'An error occurred while looking up team membership. Try refreshing the page.'
        );

        var TopicTeamsView = TeamsView.extend({
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

            checkIfUserCanCreateTeam: function() {
                var deferred = $.Deferred();
                if (this.context.userInfo.staff || this.context.userInfo.privileged) {
                    deferred.resolve(true);
                } else if (TeamUtils.isInstructorManagedTopic(this.model.attributes.type)) {
                    deferred.resolve(false);
                } else {
                    $.ajax({
                        type: 'GET',
                        url: this.context.teamMembershipsUrl,
                        data: {
                            username: this.context.userInfo.username,
                            course_id: this.context.courseID,
                            teamset_id: this.model.get('id')
                        }
                    }).done(function(data) {
                        deferred.resolve(data.count === 0);
                    }).fail(function(data) {
                        TeamUtils.parseAndShowMessage(data, canUserCreateTeamErrorMessage);
                        deferred.resolve(false);
                    });
                }
                return deferred.promise();
            },


            showActions: function() {
                HtmlUtils.append(
                    this.$el,
                    HtmlUtils.template(teamActionsTemplate)({message: actionMessage})
                );
            },

            render: function() {
                this.collection.refresh().done(_.bind(function() {
                    TeamsView.prototype.render.call(this);
                    this.checkIfUserCanCreateTeam().done(_.bind(function(canUserCreateTeam) {
                        if (canUserCreateTeam) {
                            this.showActions();
                        }
                    }, this));
                }, this));
                return this;
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
                $('html, body').animate({
                    scrollTop: 0
                }, 500);
            },

            showCreateTeamForm: function(event) {
                event.preventDefault();
                Backbone.history.navigate(
                        'topics/' + this.model.id + '/create-team',
                        {trigger: true}
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
