define([
    'jquery',
    'backbone',
    'common/js/spec_helpers/ajax_helpers',
    'teams/js/views/teams_tab'
], function ($, Backbone, AjaxHelpers, TeamsTabView) {
    'use strict';

    describe('TeamsTab', function () {
        var expectContent = function (teamsTabView, text) {
            expect(teamsTabView.$('.page-content-main').text()).toContain(text);
        };

        var expectHeader = function (teamsTabView, text) {
            expect(teamsTabView.$('.teams-header').text()).toContain(text);
        };

        var expectError = function (teamsTabView, text) {
            expect(teamsTabView.$('.warning').text()).toContain(text);
        };

        var expectFocus = function (element) {
            expect(element.focus).toHaveBeenCalled();
        };

        var createUserInfo = function(options) {
            var defaultTeamMembershipData = {
                count: 1,
                currentPage: 1,
                numPages: 1,
                next: null,
                previous: null,
                results: [
                    {
                        user: {
                            username: 'andya',
                            url: 'https://openedx.example.com/api/user/v1/accounts/andya'
                        },
                        team: {
                            description: '',
                            name: 'Discrete Maths',
                            id: 'dm',
                            topic_id: 'algorithms'
                        },
                        date_joined: '2015-04-09T17:31:56Z'
                    }
                ]
            };
            return _.extend(
                {
                    username: 'andya',
                    privileged: false,
                    teamMembershipData: defaultTeamMembershipData
                },
                options
            );
        };

        var createTeamsTabView = function(options) {
            var defaultTopics = {
                    count: 1,
                    num_pages: 1,
                    current_page: 1,
                    start: 0,
                    results: [{
                        description: 'test description',
                        name: 'test topic',
                        id: 'test_topic',
                        team_count: 0
                    }]
                },
                teamsTabView = new TeamsTabView(
                    _.extend(
                        {
                            el: $('.teams-content'),
                            topics: defaultTopics,
                            userInfo: createUserInfo(),
                            topicsUrl: 'api/topics/',
                            topicUrl: 'api/topics/topic_id,test/course/id',
                            teamsUrl: 'api/teams/',
                            courseID: 'test/course/id'
                        },
                        options || {}
                    )
                ).render();
            return teamsTabView;
        };

        beforeEach(function () {
            setFixtures('<div class="teams-content"></div>');
            spyOn($.fn, 'focus');
        });

        describe('My Teams', function() {
            it('shows the "My Teams" tab initially', function () {
                var teamsTabView = createTeamsTabView();
                expectHeader(teamsTabView, 'See all teams in your course, organized by topic');
                expectContent(teamsTabView, 'Discrete Maths');
                expect(teamsTabView.$el.text()).not.toContain('Are you having trouble finding a team to join?');
            });

            it('can switch to the "My Teams" tab', function () {
                var teamsTabView = createTeamsTabView();
                teamsTabView.$('a.nav-item[data-url="browse"]').click();
                expectContent(teamsTabView, 'test description');
                teamsTabView.$('a.nav-item[data-url="my-teams"]').click();
                expectContent(teamsTabView, 'Discrete Maths');
            });

        });

        describe('Browse Topics', function() {
            it('can switch to the "Browse" tab', function () {
                var teamsTabView = createTeamsTabView();
                teamsTabView.$('a.nav-item[data-url="my-teams"]').click();
                expectContent(teamsTabView, 'Discrete Maths');
                teamsTabView.$('a.nav-item[data-url="browse"]').click();
                expectContent(teamsTabView, 'test description');
            });
        });

        describe('Navigation', function () {
            afterEach(function () {
                Backbone.history.stop();
            });

            var lastUrl = null;
            var spyOnRouter = function(router) {
                spyOn(Backbone.history, '_updateHash').andCallFake(function (data, title, url) {
                    lastUrl = url;
                });
                Backbone.history.start();
            };

            it('displays and focuses an error message when trying to navigate to a nonexistent page', function () {
                var teamsTabView = createTeamsTabView();
                spyOnRouter();
                teamsTabView.router.navigate('no_such_page', {trigger: true});
                expectError(teamsTabView, 'The page "no_such_page" could not be found.');
                expectFocus(teamsTabView.$('.warning'));
            });

            it('displays and focuses an error message when trying to navigate to a nonexistent topic', function () {
                var requests = AjaxHelpers.requests(this),
                    teamsTabView = createTeamsTabView();
                spyOnRouter();
                teamsTabView.router.navigate('topics/no_such_topic', {trigger: true});
                AjaxHelpers.expectRequest(requests, 'GET', 'api/topics/no_such_topic,test/course/id', null);
                AjaxHelpers.respondWithError(requests, 404);
                expectError(teamsTabView, 'The topic "no_such_topic" could not be found.');
                expectFocus(teamsTabView.$('.warning'));
            });

            it('displays and focuses an error message when trying to navigate to a nonexistent team', function () {
                var requests = AjaxHelpers.requests(this),
                    teamsTabView = createTeamsTabView();
                spyOnRouter();
                teamsTabView.router.navigate('teams/test_topic/no_such_team', {trigger: true});
                AjaxHelpers.expectRequest(requests, 'GET', 'api/teams/no_such_team', null);
                AjaxHelpers.respondWithError(requests, 404);
                expectError(teamsTabView, 'The team "no_such_team" could not be found.');
                expectFocus(teamsTabView.$('.warning'));
            });
        });

        describe('Discussion privileges', function () {
            it('allows privileged access to any team', function () {
                var teamsTabView = createTeamsTabView({
                    userInfo: createUserInfo({ privileged: true })
                });
                // Note: using `undefined` here to ensure that we
                // don't even look at the team when the user is
                // privileged
                expect(teamsTabView.readOnlyDiscussion(undefined)).toBe(false);
            });

            it('allows access to a team which an unprivileged user is a member of', function () {
                var teamsTabView = createTeamsTabView({
                    userInfo: createUserInfo({
                        username: 'test-user',
                        privileged: false
                    })
                });
                expect(teamsTabView.readOnlyDiscussion({
                    attributes: {
                        membership: [{
                            user: {
                                username: 'test-user'
                            }
                        }]
                    }
                })).toBe(false);
            });

            it('does not allow access if the user is neither privileged nor a team member', function () {
                var teamsTabView = createTeamsTabView({
                    userInfo: createUserInfo({ privileged: false })
                });
                expect(teamsTabView.readOnlyDiscussion({
                    attributes: { membership: [] }
                })).toBe(true);
            });
        });
    });
});
