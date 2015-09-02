;(function (define) {
    'use strict';

    define(['backbone',
            'underscore',
            'gettext',
            'common/js/components/views/search_field',
            'js/components/header/views/header',
            'js/components/header/models/header',
            'js/components/tabbed/views/tabbed_view',
            'teams/js/models/topic',
            'teams/js/collections/topic',
            'teams/js/models/team',
            'teams/js/collections/team',
            'teams/js/collections/team_membership',
            'teams/js/views/topics',
            'teams/js/views/team_profile',
            'teams/js/views/my_teams',
            'teams/js/views/topic_teams',
            'teams/js/views/edit_team',
            'teams/js/views/team_profile_header_actions',
            'text!teams/templates/teams_tab.underscore'],
        function (Backbone, _, gettext, SearchFieldView, HeaderView, HeaderModel, TabbedView,
                  TopicModel, TopicCollection, TeamModel, TeamCollection, TeamMembershipCollection,
                  TopicsView, TeamProfileView, MyTeamsView, TopicTeamsView, TeamEditView,
                  TeamProfileHeaderActionsView, teamsTemplate) {
            var TeamsHeaderModel = HeaderModel.extend({
                initialize: function () {
                    _.extend(this.defaults, {nav_aria_label: gettext('teams')});
                    HeaderModel.prototype.initialize.call(this);
                }
            });

            var ViewWithHeader = Backbone.View.extend({
                initialize: function (options) {
                    this.header = options.header;
                    this.main = options.main;
                },

                render: function () {
                    this.$el.html(_.template(teamsTemplate));
                    this.$('p.error').hide();
                    this.header.setElement(this.$('.teams-header')).render();
                    this.main.setElement(this.$('.page-content')).render();
                    return this;
                }
            });

            var TeamTabView = Backbone.View.extend({
                initialize: function(options) {
                    var router;
                    this.context = options.context;
                    // This slightly tedious approach is necessary
                    // to use regular expressions within Backbone
                    // routes, allowing us to capture which tab
                    // name is being routed to.
                    router = this.router = new Backbone.Router();
                    _.each([
                        [':default', _.bind(this.routeNotFound, this)],
                        ['content', _.bind(function () {
                            // The backbone router unfortunately usurps the
                            // default behavior of in-page-links.  This hack
                            // prevents the screen reader in-page-link from
                            // being picked up by the backbone router.
                        }, this)],
                        ['topics/:topic_id(/)', _.bind(this.browseTopic, this)],
                        ['topics/:topic_id/search(/)', _.bind(this.searchTeams, this)],
                        ['topics/:topic_id/create-team(/)', _.bind(this.newTeam, this)],
                        ['topics/:topic_id/:team_id/edit-team(/)', _.bind(this.editTeam, this)],
                        ['teams/:topic_id/:team_id(/)', _.bind(this.browseTeam, this)],
                        [new RegExp('^(browse)\/?$'), _.bind(this.goToTab, this)],
                        [new RegExp('^(my-teams)\/?$'), _.bind(this.goToTab, this)]
                    ], function (route) {
                        router.route.apply(router, route);
                    });

                    // Create an event queue to track team changes
                    this.teamEvents = _.clone(Backbone.Events);

                    this.teamMemberships = new TeamMembershipCollection(
                        this.context.userInfo.team_memberships_data,
                        {
                            teamEvents: this.teamEvents,
                            url: this.context.teamMembershipsUrl,
                            course_id: this.context.courseID,
                            username: this.context.userInfo.username,
                            privileged: this.context.userInfo.privileged,
                            staff: this.context.userInfo.staff,
                            parse: true
                        }
                    ).bootstrap();

                    this.myTeamsView = new MyTeamsView({
                        router: this.router,
                        teamEvents: this.teamEvents,
                        context: this.context,
                        collection: this.teamMemberships,
                        teamMemberships: this.teamMemberships
                    });

                    this.topicsCollection = new TopicCollection(
                        this.context.topics,
                        {
                            teamEvents: this.teamEvents,
                            url: this.context.topicsUrl,
                            course_id: this.context.courseID,
                            parse: true
                        }
                    ).bootstrap();

                    this.topicsView = new TopicsView({
                        router: this.router,
                        teamEvents: this.teamEvents,
                        collection: this.topicsCollection
                    });

                    this.mainView = this.tabbedView = this.createViewWithHeader({
                        title: gettext("Teams"),
                        description: gettext("See all teams in your course, organized by topic. Join a team to collaborate with other learners who are interested in the same topic as you are."),
                        mainView: new TabbedView({
                            tabs: [{
                                title: gettext('My Team'),
                                url: 'my-teams',
                                view: this.myTeamsView
                            }, {
                                title: interpolate(
                                    // Translators: sr_start and sr_end surround text meant only for screen readers.
                                    // The whole string will be shown to users as "Browse teams" if they are using a
                                    // screenreader, and "Browse" otherwise.
                                    gettext("Browse %(sr_start)s teams %(sr_end)s"),
                                    {"sr_start": '<span class="sr">', "sr_end": '</span>'}, true
                                ),
                                url: 'browse',
                                view: this.topicsView
                            }],
                            router: this.router
                        })
                    });
                },

                /**
                 * Start up the Teams app
                 */
                start: function() {
                    Backbone.history.start();

                    // Navigate to the default page if there is no history:
                    // 1. If the user belongs to at least one team, jump to the "My Teams" page
                    // 2. If not, then jump to the "Browse" page
                    if (Backbone.history.getFragment() === '') {
                        if (this.teamMemberships.length > 0) {
                            this.router.navigate('my-teams', {trigger: true});
                        } else {
                            this.router.navigate('browse', {trigger: true});
                        }
                    }
                },

                render: function() {
                    this.mainView.setElement(this.$el).render();
                    this.hideWarning();
                    return this;
                },

                /**
                 * Render the list of teams for the given topic ID.
                 */
                browseTopic: function (topicID) {
                    var self = this;
                    this.getTeamsView(topicID).done(function (teamsView) {
                        self.teamsView = self.mainView = teamsView;
                        self.render();
                    });
                },

                /**
                 * Show the search results for a team.
                 */
                searchTeams: function (topicID) {
                    var view = this;
                    if (!this.teamsCollection) {
                        this.router.navigate('topics/' + topicID, {trigger: true});
                    } else {
                        this.getTopic(topicID).done(function (topic) {
                            view.mainView = view.createTeamsListView({
                                topic: topic,
                                collection: view.teamsCollection,
                                title: gettext('Team Search'),
                                description: interpolate(
                                    gettext('Showing results for "%(searchString)s"'),
                                    { searchString: view.teamsCollection.searchString },
                                    true
                                ),
                                breadcrumbs: view.createBreadcrumbs(topic),
                                showSortControls: false
                            });
                            view.render();
                        });
                    }
                },

                /**
                 * Render the create new team form.
                 */
                newTeam: function (topicID) {
                    var view = this;
                    this.getTopic(topicID).done(function (topic) {
                        view.mainView = view.createViewWithHeader({
                            topic: topic,
                            title: gettext("Create a New Team"),
                            description: gettext("Create a new team if you can't find an existing team to join, or if you would like to learn with friends you know."),
                            mainView: new TeamEditView({
                                action: 'create',
                                teamEvents: view.teamEvents,
                                context: view.context,
                                topic: topic
                            })
                        });
                        view.render();
                    });
                },

                /**
                 * Render the edit team form.
                 */
                editTeam: function (topicID, teamID) {
                    var self = this,
                        editViewWithHeader;
                    this.getTopic(topicID).done(function (topic) {
                        self.getTeam(teamID, false).done(function(team) {
                            var view = new TeamEditView({
                                action: 'edit',
                                teamEvents: self.teamEvents,
                                context: self.context,
                                topic: topic,
                                model: team
                            });
                            editViewWithHeader = self.createViewWithHeader({
                                title: gettext("Edit Team"),
                                description: gettext("If you make significant changes, make sure you notify members of the team before making these changes."),
                                mainView: view,
                                topic: topic,
                                team: team
                            });
                            self.mainView = editViewWithHeader;
                            self.render();
                        });
                    });
                },

                /**
                 * Return a promise for the TeamsView for the given topic ID.
                 */
                getTeamsView: function (topicID) {
                    // Lazily load the teams-for-topic view in
                    // order to avoid making an extra AJAX call.
                    var view = this,
                        deferred = $.Deferred();
                    if (this.teamsView && this.teamsCollection && this.teamsCollection.topic_id === topicID) {
                        this.teamsCollection.setSearchString('');
                        deferred.resolve(this.teamsView);
                    } else {
                        this.getTopic(topicID)
                            .done(function(topic) {
                                var collection = new TeamCollection([], {
                                    teamEvents: view.teamEvents,
                                    course_id: view.context.courseID,
                                    topic_id: topicID,
                                    url: view.context.teamsUrl,
                                    per_page: 10
                                });
                                view.teamsCollection = collection;
                                collection.goTo(1)
                                    .done(function() {
                                        var teamsView = view.createTeamsListView({
                                            topic: topic,
                                            collection: collection,
                                            showSortControls: true
                                        });
                                        deferred.resolve(teamsView);
                                    });
                            });
                    }
                    return deferred.promise();
                },

                createTeamsListView: function(options) {
                    var topic = options.topic,
                        collection = options.collection,
                        teamsView = new TopicTeamsView({
                            router: this.router,
                            context: this.context,
                            model: topic,
                            collection: collection,
                            teamMemberships: this.teamMemberships,
                            showSortControls: options.showSortControls
                        }),
                        searchFieldView = new SearchFieldView({
                            type: 'teams',
                            label: gettext('Search teams'),
                            collection: collection
                        }),
                        viewWithHeader = this.createViewWithHeader({
                            subject: topic,
                            mainView: teamsView,
                            headerActionsView: searchFieldView,
                            title: options.title,
                            description: options.description,
                            breadcrumbs: options.breadcrumbs
                        });
                    // Listen to requests to sync the collection and redirect it as follows:
                    // 1. If the collection includes a search, show the search results page
                    // 2. If not, then show the regular topic teams page
                    // Note: Backbone makes this a no-op if redirecting to the current page.
                    this.listenTo(collection, 'sync', function() {
                        if (collection.searchString) {
                            Backbone.history.navigate('topics/' + topic.get('id') + '/search', {trigger: true});
                        } else {
                            Backbone.history.navigate('topics/' + topic.get('id'), {trigger: true});
                        }
                    });
                    return viewWithHeader;
                },

                /**
                 * Browse to the team with the specified team ID belonging to the specified topic.
                 */
                browseTeam: function (topicID, teamID) {
                    var self = this;
                    this.getBrowseTeamView(topicID, teamID).done(function (browseTeamView) {
                        self.mainView = browseTeamView;
                        self.render();
                    });
                },

                /**
                 * Sets focus to teams header.
                 */
                setFocusToHeader: function() {
                    $('.page-header-main .sr-is-focusable').focus();
                },

                /**
                 * Return a promise for the team view for the given team ID.
                 */
                getBrowseTeamView: function (topicID, teamID) {
                    var self = this,
                        deferred = $.Deferred();
                    self.getTopic(topicID).done(function(topic) {
                        self.getTeam(teamID, true).done(function(team) {
                            var view = new TeamProfileView({
                                teamEvents: self.teamEvents,
                                router: self.router,
                                context: self.context,
                                model: team,
                                setFocusToHeaderFunc: self.setFocusToHeader
                            });

                            var TeamProfileActionsView = new TeamProfileHeaderActionsView({
                                teamEvents: self.teamEvents,
                                context: self.context,
                                model: team,
                                topic: topic,
                                showEditButton: self.context.userInfo.privileged || self.context.userInfo.staff
                            });
                            deferred.resolve(
                                self.createViewWithHeader(
                                    {
                                        mainView: view,
                                        subject: team,
                                        topic: topic,
                                        headerActionsView: TeamProfileActionsView
                                    }
                                )
                            );
                        });
                    });
                    return deferred.promise();
                },

                createBreadcrumbs: function(topic, team) {
                    var breadcrumbs = [{
                        title: gettext('All Topics'),
                        url: '#browse'
                    }];
                    if (topic) {
                        breadcrumbs.push({
                            title: topic.get('name'),
                            url: '#topics/' + topic.id
                        });
                        if (team) {
                            breadcrumbs.push({
                                title: team.get('name'),
                                url: '#teams/' + topic.id + '/' + team.id
                            });
                        }
                    }
                    return breadcrumbs;
                },

                createHeaderModel: function(options) {
                    var subject = options.subject,
                        breadcrumbs = options.breadcrumbs,
                        title = options.title || subject.get('name'),
                        description = options.description || subject.get('description');
                    if (!breadcrumbs) {
                        breadcrumbs = this.createBreadcrumbs(options.topic, options.team);
                    }
                    return new TeamsHeaderModel({
                        breadcrumbs: breadcrumbs,
                        title: title,
                        description: description
                    });
                },

                createViewWithHeader: function(options) {
                    var router = this.router;
                    return new ViewWithHeader({
                        header: new HeaderView({
                            model: this.createHeaderModel(options),
                            headerActionsView: options.headerActionsView,
                            events: {
                                'click nav.breadcrumbs a.nav-item': function (event) {
                                    var url = $(event.currentTarget).attr('href');
                                    event.preventDefault();
                                    router.navigate(url, {trigger: true});
                                }
                            }
                        }),
                        main: options.mainView
                    });
                },

                /**
                 * Get a topic given a topic ID.  Returns a jQuery deferred
                 * promise, since the topic may need to be fetched from the
                 * server.
                 * @param topicID the string identifier for the requested topic
                 * @returns a jQuery deferred promise for the topic.
                 */
                getTopic: function (topicID) {
                    // Try finding topic in the current page of the
                    // topicCollection.  Otherwise call the topic endpoint.
                    var topic = this.topicsCollection.findWhere({'id': topicID}),
                        self = this,
                        deferred = $.Deferred();
                    if (topic) {
                        deferred.resolve(topic);
                    } else {
                        topic = new TopicModel({
                            id: topicID,
                            url: self.context.topicUrl.replace('topic_id', topicID)
                        });
                        topic.fetch()
                            .done(function() {
                                deferred.resolve(topic);
                            })
                            .fail(function() {
                                self.topicNotFound(topicID);
                                deferred.reject();
                            });
                    }
                    return deferred.promise();
                },

                /**
                 * Get a team given a team ID.  Returns a jQuery deferred
                 * promise, since the team may need to be fetched from the
                 * server.
                 * @param teamID the string identifier for the requested team
                 * @param expandUser bool to add the users info.
                 * @returns {promise} a jQuery deferred promise for the team.
                 */
                getTeam: function (teamID, expandUser) {
                    var team = this.teamsCollection ? this.teamsCollection.get(teamID) : null,
                        self = this,
                        deferred = $.Deferred(),
                        teamUrl = this.context.teamsUrl + teamID + (expandUser ? '?expand=user': '');
                    if (team) {
                        team.url = teamUrl;
                        deferred.resolve(team);
                    } else {
                        team = new TeamModel({
                            id: teamID,
                            url: teamUrl
                        });
                        team.fetch()
                            .done(function() {
                                deferred.resolve(team);
                            })
                            .fail(function() {
                                self.teamNotFound(teamID);
                                deferred.reject();
                            });
                    }
                    return deferred.promise();
                },

                /**
                 * Set up the tabbed view and switch tabs.
                 */
                goToTab: function (tab) {
                    this.mainView = this.tabbedView;
                    // Note that `render` should be called first so
                    // that the tabbed view's element is set
                    // correctly.
                    this.render();
                    this.tabbedView.main.setActiveTab(tab);
                },

                // Error handling

                routeNotFound: function (route) {
                    this.notFoundError(
                        interpolate(
                            gettext('The page "%(route)s" could not be found.'),
                            {route: route},
                            true
                        )
                    );
                },

                topicNotFound: function (topicID) {
                    this.notFoundError(
                        interpolate(
                            gettext('The topic "%(topic)s" could not be found.'),
                            {topic: topicID},
                            true
                        )
                    );
                },

                teamNotFound: function (teamID) {
                    this.notFoundError(
                        interpolate(
                            gettext('The team "%(team)s" could not be found.'),
                            {team: teamID},
                            true
                        )
                    );
                },

                /**
                 * Called when the user attempts to navigate to a
                 * route that doesn't exist. "Redirects" back to
                 * the main teams tab, and adds an error message.
                 */
                notFoundError: function (message) {
                    this.router.navigate('my-teams', {trigger: true});
                    this.showWarning(message);
                },

                showWarning: function (message) {
                    var warningEl = this.$('.warning');
                    warningEl.find('.copy').html('<p>' + message + '</p');
                    warningEl.toggleClass('is-hidden', false);
                    warningEl.focus();
                },

                hideWarning: function () {
                    this.$('.warning').toggleClass('is-hidden', true);
                },

                /**
                 * Returns true if the discussion thread belonging to
                 * `team` is accessible to the user. This is the case
                 * if the user is privileged (i.e., a community TA,
                 * moderator, or administrator), or if the user
                 * belongs to the team.
                 */
                readOnlyDiscussion: function (team) {
                    var userInfo = this.context.userInfo;
                    return !(
                        userInfo.privileged ||
                        _.any(team.attributes.membership, function (membership) {
                            return membership.user.username === userInfo.username;
                        })
                    );
                }
            });

            return TeamTabView;
        });
}).call(this, define || RequireJS.define);
