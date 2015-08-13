;(function (define) {
    'use strict';

    define(['backbone',
            'underscore',
            'gettext',
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
            'teams/js/views/team_join',
            'text!teams/templates/teams_tab.underscore'],
        function (Backbone, _, gettext, HeaderView, HeaderModel, TabbedView,
                  TopicModel, TopicCollection, TeamModel, TeamCollection, TeamMembershipCollection,
                  TopicsView, TeamProfileView, MyTeamsView, TopicTeamsView, TeamEditView,
                  TeamJoinView, teamsTemplate) {
            var TeamsHeaderModel = HeaderModel.extend({
                initialize: function (attributes) {
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
                    this.courseID = options.courseID;
                    this.topics = options.topics;
                    this.topicUrl = options.topicUrl;
                    this.teamsUrl = options.teamsUrl;
                    this.teamMembershipsUrl = options.teamMembershipsUrl;
                    this.teamMembershipDetailUrl = options.teamMembershipDetailUrl;
                    this.maxTeamSize = options.maxTeamSize;
                    this.languages = options.languages;
                    this.countries = options.countries;
                    this.userInfo = options.userInfo;
                    this.teamsBaseUrl = options.teamsBaseUrl;
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
                        ['topics/:topic_id/create-team(/)', _.bind(this.newTeam, this)],
                        ['teams/:topic_id/:team_id(/)', _.bind(this.browseTeam, this)],
                        [new RegExp('^(browse)\/?$'), _.bind(this.goToTab, this)],
                        [new RegExp('^(my-teams)\/?$'), _.bind(this.goToTab, this)]
                    ], function (route) {
                        router.route.apply(router, route);
                    });

                    this.teamMemberships = new TeamMembershipCollection(
                        this.userInfo.team_memberships_data,
                        {
                            url: this.teamMembershipsUrl,
                            course_id: this.courseID,
                            username: this.userInfo.username,
                            privileged: this.userInfo.privileged,
                            parse: true
                        }
                    ).bootstrap();

                    this.myTeamsView = new MyTeamsView({
                        router: this.router,
                        collection: this.teamMemberships,
                        teamMemberships: this.teamMemberships,
                        maxTeamSize: this.maxTeamSize,
                        teamParams: {
                            courseID: this.courseID,
                            teamsUrl: this.teamsUrl,
                            languages: this.languages,
                            countries: this.countries
                        }
                    });

                    this.topicsCollection = new TopicCollection(
                        this.topics,
                        {url: options.topicsUrl, course_id: this.courseID, parse: true}
                    ).bootstrap();

                    this.topicsView = new TopicsView({
                        collection: this.topicsCollection,
                        router: this.router
                    });

                    this.mainView = this.tabbedView = new ViewWithHeader({
                        header: new HeaderView({
                            model: new TeamsHeaderModel({
                                description: gettext("See all teams in your course, organized by topic. Join a team to collaborate with other learners who are interested in the same topic as you are."),
                                title: gettext("Teams")
                            })
                        }),
                        main: new TabbedView({
                            tabs: [{
                                title: gettext('My Team'),
                                url: 'my-teams',
                                view: this.myTeamsView
                            }, {
                                title: interpolate(
                                    // Translators: sr_start and sr_end surround text meant only for screen readers.  The whole string will be shown to users as "Browse teams" if they are using a screenreader, and "Browse" otherwise.
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
                 * Render the create new team form.
                 */
                newTeam: function (topicID) {
                    var self = this;
                    this.getTeamsView(topicID).done(function (teamsView) {
                        self.mainView = new ViewWithHeader({
                            header: new HeaderView({
                                model: new TeamsHeaderModel({
                                    description: gettext("Create a new team if you can't find existing teams to join, or if you would like to learn with friends you know."),
                                    title: gettext("Create a New Team"),
                                    breadcrumbs: [
                                        {
                                            title: teamsView.main.teamParams.topicName,
                                            url: '#topics/' + teamsView.main.teamParams.topicID
                                        }
                                    ]
                                })
                            }),
                            main: new TeamEditView({
                                tagName: 'create-new-team',
                                teamParams: teamsView.main.teamParams,
                                primaryButtonTitle: 'Create'
                            })
                        });
                        self.render();
                    });
                },

                /**
                 * Return a promise for the TeamsView for the given topic ID.
                 */
                getTeamsView: function (topicID) {
                    // Lazily load the teams-for-topic view in
                    // order to avoid making an extra AJAX call.
                    var self = this,
                        router = this.router,
                        deferred = $.Deferred();
                    if (this.teamsCollection && this.teamsCollection.topic_id === topicID) {
                        deferred.resolve(this.teamsView);
                    } else {
                        this.getTopic(topicID)
                            .done(function(topic) {
                                var collection = new TeamCollection([], {
                                    course_id: self.courseID,
                                    topic_id: topicID,
                                    url: self.teamsUrl,
                                    per_page: 10
                                });
                                self.teamsCollection = collection;
                                collection.goTo(1)
                                    .done(function() {
                                        var teamsView = new TopicTeamsView({
                                            router: router,
                                            topic: topic,
                                            collection: collection,
                                            teamMemberships: self.teamMemberships,
                                            maxTeamSize: self.maxTeamSize,
                                            teamParams: {
                                                courseID: self.courseID,
                                                topicID: topic.get('id'),
                                                teamsUrl: self.teamsUrl,
                                                topicName: topic.get('name'),
                                                languages: self.languages,
                                                countries: self.countries
                                            }
                                        });
                                        deferred.resolve(
                                            self.createViewWithHeader(
                                                {
                                                    mainView: teamsView,
                                                    subject: topic
                                                }
                                            )
                                        );
                                    });
                            });
                    }
                    return deferred.promise();
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
                 * Return a promise for the team view for the given team ID.
                 */
                getBrowseTeamView: function (topicID, teamID) {
                    var self = this,
                        deferred = $.Deferred(),
                        courseID = this.courseID;
                    self.getTopic(topicID).done(function(topic) {
                        self.getTeam(teamID, true).done(function(team) {
                            var view = new TeamProfileView({
                                    courseID: courseID,
                                    model: team,
                                    maxTeamSize: self.maxTeamSize,
                                    isPrivileged: self.userInfo.privileged,
                                    requestUsername: self.userInfo.username,
                                    countries: self.countries,
                                    languages: self.languages,
                                    teamInviteUrl: self.teamsBaseUrl + '#teams/' + topicID + '/' + teamID + '?invite=true',
                                    teamMembershipDetailUrl: self.teamMembershipDetailUrl
                                });
                            var teamJoinView = new TeamJoinView(
                                {
                                    model: team,
                                    teamsUrl: self.teamsUrl,
                                    maxTeamSize: self.maxTeamSize,
                                    currentUsername: self.userInfo.username,
                                    teamMembershipsUrl: self.teamMembershipsUrl
                                }
                            );
                            deferred.resolve(
                                self.createViewWithHeader(
                                    {
                                        mainView: view,
                                        subject: team,
                                        parentTopic: topic,
                                        headerActionsView: teamJoinView
                                    }
                                )
                            );
                        });
                    });
                    return deferred.promise();
                },

                createViewWithHeader: function (options) {
                    var router = this.router,
                        breadcrumbs, headerView;
                    breadcrumbs = [{
                        title: gettext('All Topics'),
                        url: '#browse'
                    }];
                    if (options.parentTopic) {
                        breadcrumbs.push({
                            title: options.parentTopic.get('name'),
                            url: '#topics/' + options.parentTopic.id
                        });
                    }
                    headerView = new HeaderView({
                        model: new TeamsHeaderModel({
                            description: options.subject.get('description'),
                            title: options.subject.get('name'),
                            breadcrumbs: breadcrumbs
                        }),
                        headerActionsView: options.headerActionsView,
                        events: {
                            'click nav.breadcrumbs a.nav-item': function (event) {
                                var url = $(event.currentTarget).attr('href');
                                event.preventDefault();
                                router.navigate(url, {trigger: true});
                            }
                        }
                    });
                    return new ViewWithHeader({
                        header: headerView,
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
                            url: self.topicUrl.replace('topic_id', topicID)
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
                        teamUrl = this.teamsUrl + teamID + (expandUser ? '?expand=user': '');
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
                    var self = this;
                    return !(
                        self.userInfo.privileged ||
                        _.any(team.attributes.membership, function (membership) {
                            return membership.user.username === self.userInfo.username;
                        })
                    );
                }
            });

            return TeamTabView;
        });
}).call(this, define || RequireJS.define);
