(function(define) {
    'use strict';
    define([
        'underscore',
        'backbone',
        'gettext',
        'edx-ui-toolkit/js/utils/html-utils',
        'teams/js/views/teams',
        'common/js/components/views/paging_header',
        'text!teams/templates/team-actions.underscore'
    ], function(_, Backbone, gettext, HtmlUtils, TeamsView, PagingHeader, teamActionsTemplate) {
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
                this.myTeamsCollection = options.myTeamsCollection;
                TeamsView.prototype.initialize.call(this, options);
            },

            canUserCreateTeam: function() {
                // Note: non-staff and non-privileged users are automatically added to any team
                // that they create. This means that if multiple team membership is
                // disabled that they cannot create a new team when they already
                // belong to one.
                return this.context.staff || this.context.privileged || this.myTeamsCollection.length === 0;
            },

            render: function() {
                var self = this;
                this.collection.refresh().done(function() {
                    var messageHtml;
                    TeamsView.prototype.render.call(self);
                    if (self.canUserCreateTeam()) {
                        messageHtml = HtmlUtils.interpolateHtml(
                            // Translators: this string is shown at the bottom of the teams page
                            // to find a team to join or else to create a new one. There are three
                            // links that need to be included in the message:
                            // 1. Browse teams in other topics
                            // 2. search teams
                            // 3. create a new team
                            // Be careful to start each link with the appropriate start indicator
                            // (e.g. {browse_span_start} for #1) and finish it with {span_end}.
                            gettext('{browse_span_start}Browse teams in other topics{span_end} or {search_span_start}search teams{span_end} in this topic. If you still can\'t find a team to join, {create_span_start}create a new team in this topic{span_end}.'),  // eslint-disable-line max-len
                            {
                                browse_span_start: HtmlUtils.HTML('<a class="browse-teams" href="">'),
                                search_span_start: HtmlUtils.HTML('<a class="search-teams" href="">'),
                                create_span_start: HtmlUtils.HTML('<a class="create-team" href="">'),
                                span_end: HtmlUtils.HTML('</a>')
                            }
                        );
                        HtmlUtils.append(
                            self.$el,
                            HtmlUtils.template(teamActionsTemplate)({messageHtml: messageHtml})
                        );
                    }
                });
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
            }
        });

        return TopicTeamsView;
    });
}).call(this, define || RequireJS.define);
