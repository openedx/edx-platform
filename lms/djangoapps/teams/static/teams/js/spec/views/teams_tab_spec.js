define([
    'jquery',
    'backbone',
    'logger',
    'edx-ui-toolkit/js/utils/spec-helpers/spec-helpers',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
    'common/js/spec_helpers/page_helpers',
    'teams/js/views/teams_tab',
    'teams/js/spec_helpers/team_spec_helpers'
], function($, Backbone, Logger, SpecHelpers, AjaxHelpers, PageHelpers, TeamsTabView, TeamSpecHelpers) {
    'use strict';

    describe('TeamsTab', function() {
        var requests;

        var expectError = function(teamsTabView, text) {
            expect(teamsTabView.$('.warning').text()).toContain(text);
        };

        var expectFocus = function(element) {
            expect(element.focus).toHaveBeenCalled();
        };

        var verifyTeamsRequest = function(options) {
            AjaxHelpers.expectRequestURL(requests, TeamSpecHelpers.testContext.teamsUrl,
                _.extend(
                    {
                        topic_id: TeamSpecHelpers.testTopicID,
                        expand: 'user',
                        course_id: TeamSpecHelpers.testCourseID,
                        order_by: '',
                        page: '1',
                        page_size: '10',
                        text_search: ''
                    },
                    options
                ));
        };

        var createTeamsTabView = function(test, options) {
            var teamsTabView = new TeamsTabView(
                {
                    el: $('.teams-content'),
                    context: TeamSpecHelpers.createMockContext(options)
                }
            );
            requests = AjaxHelpers.requests(test);
            PageHelpers.preventBackboneChangingUrl();
            teamsTabView.start();
            return teamsTabView;
        };

        beforeEach(function() {
            setFixtures('<div class="teams-content"></div>');
            spyOn($.fn, 'focus');
            spyOn(Logger, 'log');
        });

        afterEach(function() {
              Backbone.history.stop();
              $(document).off('ajaxError', TeamsTabView.prototype.errorHandler);
          }
        );

        describe('Navigation', function() {
            it('does not render breadcrumbs for the top level tabs', function() {
                var teamsTabView = createTeamsTabView(this);
                teamsTabView.router.navigate('#my-teams', {trigger: true});
                expect(teamsTabView.$('.breadcrumbs').length).toBe(0);
                teamsTabView.router.navigate('#browse', {trigger: true});
                expect(teamsTabView.$('.breadcrumbs').length).toBe(0);
            });

            it('does not interfere with anchor links to #main', function () {
                var teamsTabView = createTeamsTabView(this);
                teamsTabView.router.navigate('#main', {trigger: true});
                expect(teamsTabView.$('.wrapper-msg')).toHaveClass('is-hidden');
            });

            it('displays and focuses an error message when trying to navigate to a nonexistent page', function() {
                var teamsTabView = createTeamsTabView(this);
                teamsTabView.router.navigate('no_such_page', {trigger: true});
                expectError(teamsTabView, 'The page "no_such_page" could not be found.');
                expectFocus(teamsTabView.$('.warning'));
            });

            it('displays and focuses an error message when trying to navigate to a nonexistent topic', function() {
                var teamsTabView = createTeamsTabView(this);
                teamsTabView.router.navigate('topics/no_such_topic', {trigger: true});
                AjaxHelpers.expectRequest(requests, 'GET', '/api/team/v0/topics/no_such_topic,course/1', null);
                AjaxHelpers.respondWithError(requests, 404);
                expectError(teamsTabView, 'The topic "no_such_topic" could not be found.');
                expectFocus(teamsTabView.$('.warning'));
            });

            it('displays and focuses an error message when trying to navigate to a nonexistent team', function() {
                var teamsTabView = createTeamsTabView(this);
                teamsTabView.router.navigate('teams/' + TeamSpecHelpers.testTopicID + '/no_such_team', {trigger: true});
                AjaxHelpers.expectRequest(requests, 'GET', '/api/team/v0/teams/no_such_team?expand=user', null);
                AjaxHelpers.respondWithError(requests, 404);
                expectError(teamsTabView, 'The team "no_such_team" could not be found.');
                expectFocus(teamsTabView.$('.warning'));
            });

            it('displays and focuses an error message when it receives a 401 AJAX response', function() {
                var teamsTabView = createTeamsTabView(this).render();
                teamsTabView.router.navigate('topics/' + TeamSpecHelpers.testTopicID, {trigger: true});
                AjaxHelpers.respondWithError(requests, 401);
                expectError(teamsTabView, 'Your request could not be completed. Reload the page and try again.');
                expectFocus(teamsTabView.$('.warning'));
            });

            it('displays and focuses an error message when it receives a 500 AJAX response', function() {
                var teamsTabView = createTeamsTabView(this).render();
                teamsTabView.router.navigate('topics/' + TeamSpecHelpers.testTopicID, {trigger: true});
                AjaxHelpers.respondWithError(requests, 500);
                expectError(
                    teamsTabView,
                    'Your request could not be completed due to a server problem. Reload the page and try again. ' +
                    'If the issue persists, click the Help tab to report the problem.'
                );
                expectFocus(teamsTabView.$('.warning'));
            });

            it('does not navigate to the topics page when syncing its collection if not on search page', function() {
                var teamsTabView = createTeamsTabView(this),
                    collection = TeamSpecHelpers.createMockTeams();
                teamsTabView.createTeamsListView({
                    collection: collection,
                    topic: TeamSpecHelpers.createMockTopic()
                });
                spyOn(Backbone.history, 'navigate');
                collection.trigger('sync');
                expect(Backbone.history.navigate).not.toHaveBeenCalled();
            });
        });

        describe('Analytics Events', function() {
            SpecHelpers.withData({
                'fires a page view event for the topic page': [
                    'topics/' + TeamSpecHelpers.testTopicID,
                    {
                        page_name: 'single-topic',
                        topic_id: TeamSpecHelpers.testTopicID,
                        team_id: null
                    }
                ],
                'fires a page view event for the team page': [
                    'teams/' + TeamSpecHelpers.testTopicID + '/test_team_id',
                    {
                        page_name: 'single-team',
                        topic_id: TeamSpecHelpers.testTopicID,
                        team_id: 'test_team_id'
                    }
                ],
                'fires a page view event for the search team page': [
                    'topics/' + TeamSpecHelpers.testTopicID + '/search',
                    {
                        page_name: 'search-teams',
                        topic_id: TeamSpecHelpers.testTopicID,
                        team_id: null
                    }
                ],
                'fires a page view event for the new team page': [
                    'topics/' + TeamSpecHelpers.testTopicID + '/create-team',
                    {
                        page_name: 'new-team',
                        topic_id: TeamSpecHelpers.testTopicID,
                        team_id: null
                    }
                ],
                'fires a page view event for the edit team page': [
                    'teams/' + TeamSpecHelpers.testTopicID + '/' + 'test_team_id/edit-team',
                    {
                        page_name: 'edit-team',
                        topic_id: TeamSpecHelpers.testTopicID,
                        team_id: 'test_team_id'
                    }
                ]
            }, function(url, expectedEvent) {
                var teamsTabView = createTeamsTabView(this, {
                    userInfo: TeamSpecHelpers.createMockUserInfo({staff: true})
                });
                teamsTabView.teamsCollection = TeamSpecHelpers.createMockTeams();
                teamsTabView.router.navigate(url, {trigger: true});
                if (requests.length > requests.currentIndex) {
                    AjaxHelpers.respondWithJson(requests, {});
                }
                expect(Logger.log).toHaveBeenCalledWith('edx.team.page_viewed', expectedEvent);
            });
        });

        describe('Discussion privileges', function() {
            it('allows privileged access to any team', function() {
                var teamsTabView = createTeamsTabView(this, {
                        userInfo: TeamSpecHelpers.createMockUserInfo({privileged: true})
                    });
                // Note: using `undefined` here to ensure that we
                // don't even look at the team when the user is
                // privileged
                expect(teamsTabView.readOnlyDiscussion(undefined)).toBe(false);
            });

            it('allows access to a team which an unprivileged user is a member of', function() {
                var teamsTabView = createTeamsTabView(this, {
                        userInfo: TeamSpecHelpers.createMockUserInfo({
                            username: TeamSpecHelpers.testUser,
                            privileged: false
                        })
                    });
                expect(teamsTabView.readOnlyDiscussion({
                    attributes: {
                        membership: [{
                            user: {
                                username: TeamSpecHelpers.testUser
                            }
                        }]
                    }
                })).toBe(false);
            });

            it('does not allow access if the user is neither privileged nor a team member', function() {
                var teamsTabView = createTeamsTabView(this, {
                        userInfo: TeamSpecHelpers.createMockUserInfo({privileged: false, staff: true})
                    });
                expect(teamsTabView.readOnlyDiscussion({
                    attributes: {membership: []}
                })).toBe(true);
            });
        });

        describe('Search', function() {
            var performSearch = function(requests, teamsTabView) {
                teamsTabView.$('.search-field').val('foo');
                teamsTabView.$('.action-search').click();
                verifyTeamsRequest({
                    order_by: '',
                    text_search: 'foo'
                });
                AjaxHelpers.respondWithJson(requests, TeamSpecHelpers.createMockTeamsResponse({results: []}));

                // Expect exactly one search request to be fired
                AjaxHelpers.expectNoRequests(requests);
            };

            it('can search teams', function() {
                var teamsTabView = createTeamsTabView(this);
                teamsTabView.browseTopic(TeamSpecHelpers.testTopicID);
                verifyTeamsRequest({
                    order_by: 'last_activity_at',
                    text_search: ''
                });
                AjaxHelpers.respondWithJson(requests, {});
                performSearch(requests, teamsTabView);
                expect(teamsTabView.$('.page-title').text()).toBe('Team Search');
                expect(teamsTabView.$('.page-description').text()).toBe('Showing results for "foo"');
            });

            it('can clear a search', function() {
                var teamsTabView = createTeamsTabView(this);
                teamsTabView.browseTopic(TeamSpecHelpers.testTopicID);
                AjaxHelpers.respondWithJson(requests, {});

                // Perform a search
                performSearch(requests, teamsTabView);

                // Clear the search and submit it again
                teamsTabView.$('.search-field').val('');
                teamsTabView.$('.action-search').click();
                
                verifyTeamsRequest({
                    order_by: 'last_activity_at'
                });
                AjaxHelpers.respondWithJson(requests, {});
                expect(teamsTabView.$('.page-title').text()).toBe('Test Topic 1');
                expect(teamsTabView.$('.page-description').text()).toBe('Test description 1');
            });

            it('can navigate back to all teams from a search', function() {
                var teamsTabView = createTeamsTabView(this);
                teamsTabView.browseTopic(TeamSpecHelpers.testTopicID);
                AjaxHelpers.respondWithJson(requests, {});

                // Perform a search
                performSearch(requests, teamsTabView);

                // Verify the breadcrumbs have a link back to the teams list, and click on it
                expect(teamsTabView.$('.breadcrumbs a').length).toBe(2);
                teamsTabView.$('.breadcrumbs a').last().click();
                verifyTeamsRequest({
                    order_by: 'last_activity_at',
                    text_search: ''
                });
                AjaxHelpers.respondWithJson(requests, {});
                expect(teamsTabView.$('.page-title').text()).toBe('Test Topic 1');
                expect(teamsTabView.$('.page-description').text()).toBe('Test description 1');
            });

            it('does not switch to showing results when the search returns an error', function() {
                var teamsTabView = createTeamsTabView(this);
                teamsTabView.browseTopic(TeamSpecHelpers.testTopicID);
                AjaxHelpers.respondWithJson(requests, {});

                // Perform a search but respond with a 500
                teamsTabView.$('.search-field').val('foo');
                teamsTabView.$('.action-search').click();
                AjaxHelpers.respondWithError(requests);

                // Verify that the team list is still shown
                expect(teamsTabView.$('.page-title').text()).toBe('Test Topic 1');
                expect(teamsTabView.$('.page-description').text()).toBe('Test description 1');
                expect(teamsTabView.$('.search-field').val(), 'foo');
            });
        });
    });
});
