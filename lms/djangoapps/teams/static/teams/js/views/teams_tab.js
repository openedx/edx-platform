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
            'teams/js/views/topics',
            'teams/js/views/team_profile',
            'teams/js/views/teams',
            'teams/js/views/edit_team',
            'text!teams/templates/teams_tab.underscore'],
        function (Backbone, _, gettext, HeaderView, HeaderModel, TabbedView,
                  TopicModel, TopicCollection, TeamModel, TeamCollection,
                  TopicsView, TeamProfileView, TeamsView, TeamEditView,
                  teamsTemplate) {
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
                    var TempTabView, router;
                    this.courseID = options.courseID;
                    this.topics = options.topics;
                    this.topicUrl = options.topicUrl;
                    this.teamsUrl = options.teamsUrl;
                    this.maxTeamSize = options.maxTeamSize;
                    this.languages = options.languages;
                    this.countries = options.countries;
                    // This slightly tedious approach is necessary
                    // to use regular expressions within Backbone
                    // routes, allowing us to capture which tab
                    // name is being routed to
                    router = this.router = new Backbone.Router();
                    _.each([
                        [':default', _.bind(this.routeNotFound, this)],
                        ['topics/:topic_id(/)', _.bind(this.browseTopic, this)],
                        ['topics/:topic_id/create-team(/)', _.bind(this.newTeam, this)],
                        ['teams/:topic_id/:team_id(/)', _.bind(this.browseTeam, this)],
                        [new RegExp('^(browse)\/?$'), _.bind(this.goToTab, this)],
                        [new RegExp('^(teams)\/?$'), _.bind(this.goToTab, this)]
                    ], function (route) {
                        router.route.apply(router, route);
                    });
                    // TODO replace this with actual views!
                    TempTabView = Backbone.View.extend({
                        initialize: function (options) {
                            this.text = options.text;
                        },
                        render: function () {
                            this.$el.html(this.text);
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
                            model: new HeaderModel({
                                description: gettext("See all teams in your course, organized by topic. Join a team to collaborate with other learners who are interested in the same topic as you are."),
                                title: gettext("Teams")
                            })
                        }),
                        main: new TabbedView({
                            tabs: [{
                                title: gettext('My Teams'),
                                url: 'teams',
                                view: new TempTabView({text: '<p class="temp-tab-view">This is the new Teams tab.</p>'})
                            }, {
                                title: gettext('Browse'),
                                url: 'browse',
                                view: this.topicsView
                            }],
                            router: this.router
                        })
                    });
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
                newTeam: function (topicId) {
                    var self = this;
                    this.getTeamsView(topicId).done(function (teamsView) {
                        self.mainView = new ViewWithHeader({
                            header: new HeaderView({
                                model: new HeaderModel({
                                    description: gettext("Create a new team if you can't find existing teams to join, or if you would like to learn with friends you know."),
                                    title: gettext("Create a New Team"),
                                    breadcrumbs: [
                                        {
                                            title: teamsView.main.teamParams.topicName,
                                            url: '#topics/' + teamsView.main.teamParams.topicId
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
                                this.teamsCollection = collection;
                                collection.goTo(1)
                                    .done(function() {
                                        var teamsView = new TeamsView({
                                            router: router,
                                            topic: topic,
                                            collection: collection,
                                            maxTeamSize: self.maxTeamSize,
                                            teamParams: {
                                                courseId: self.courseID,
                                                teamsUrl: self.teamsUrl,
                                                topicId: topic.get('id'),
                                                topicName: topic.get('name'),
                                                languages: self.languages,
                                                countries: self.countries
                                            }
                                        });
                                        deferred.resolve(self.createViewWithHeader(teamsView, topic));
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
                        self.getTeam(teamID).done(function(team) {
                            var readOnly = self.readOnlyDiscussion(team),
                                view = new TeamProfileView({
                                    courseID: courseID,
                                    model: team,
                                    readOnly: readOnly
                                });
                            deferred.resolve(self.createViewWithHeader(view, team, topic));
                        });
                    });
                    return deferred.promise();
                },

                createViewWithHeader: function (mainView, subject, parentTopic) {
                    var router = this.router,
                        breadcrumbs, headerView;
                    breadcrumbs = [{
                        title: gettext('All Topics'),
                        url: '#browse'
                    }];
                    if (parentTopic) {
                        breadcrumbs.push({
                            title: parentTopic.get('name'),
                            url: '#topics/' + parentTopic.id
                        });
                    }
                    headerView = new HeaderView({
                        model: new HeaderModel({
                            description: subject.get('description'),
                            title: subject.get('name'),
                            breadcrumbs: breadcrumbs
                        }),
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
                        main: mainView
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
                 * @returns {promise} a jQuery deferred promise for the team.
                 */
                getTeam: function (teamID) {
                    var team = this.teamsCollection ? this.teamsCollection.get(teamID) : null,
                        self = this,
                        deferred = $.Deferred();
                    if (team) {
                        deferred.resolve(team);
                    } else {
                        team = new TeamModel({
                            id: teamID,
                            url: this.teamsUrl + teamID
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
                    this.router.navigate('teams', {trigger: true});
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
                        this.$el.data('privileged') ||
                        _.any(team.attributes.membership, function (membership) {
                            return membership.user.username === self.$el.data('username');
                        })
                    );
                }
            });

            return TeamTabView;
        });
}).call(this, define || RequireJS.define);
