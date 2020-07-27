define([
    'jquery',
    'underscore',
    'backbone',
    'logger',
    'edx-ui-toolkit/js/utils/spec-helpers/spec-helpers',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
    'common/js/spec_helpers/page_helpers',
    'teams/js/views/teams_tab',
    'teams/js/spec_helpers/team_spec_helpers'
], function($, _, Backbone, Logger, SpecHelpers, AjaxHelpers, PageHelpers, TeamsTabView, TeamSpecHelpers) {
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

        var createTeamsTabView = function(options) {
            var teamsTabView = new TeamsTabView(
                {
                    el: $('.teams-content'),
                    context: TeamSpecHelpers.createMockContext(options)
                }
            );
            requests = AjaxHelpers.requests();
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
                var teamsTabView = createTeamsTabView();
                teamsTabView.router.navigate('#my-teams', {trigger: true});
                expect(teamsTabView.$('.breadcrumbs').length).toBe(0);
                teamsTabView.router.navigate('#browse', {trigger: true});
                expect(teamsTabView.$('.breadcrumbs').length).toBe(0);
            });

            it('does not interfere with anchor links to #main', function() {
                var teamsTabView = createTeamsTabView();
                teamsTabView.router.navigate('#main', {trigger: true});
                expect(teamsTabView.$('.wrapper-msg')).toHaveClass('is-hidden');
            });

            it('displays and focuses an error message when trying to navigate to a nonexistent page', function() {
                var teamsTabView = createTeamsTabView();
                teamsTabView.router.navigate('no_such_page', {trigger: true});
                expectError(teamsTabView, 'The page "no_such_page" could not be found.');
                expectFocus(teamsTabView.$('.warning'));
            });

            it('displays and focuses an error message when trying to navigate to a nonexistent topic', function() {
                var teamsTabView = createTeamsTabView();
                teamsTabView.router.navigate('topics/no_such_topic', {trigger: true});
                AjaxHelpers.expectRequest(requests, 'GET', '/api/team/v0/topics/no_such_topic,course/1', null);
                AjaxHelpers.respondWithError(requests, 404);
                expectError(teamsTabView, 'The topic "no_such_topic" could not be found.');
                expectFocus(teamsTabView.$('.warning'));
            });

            it('displays and focuses an error message when trying to navigate to a nonexistent team', function() {
                var teamsTabView = createTeamsTabView();
                teamsTabView.router.navigate('teams/' + TeamSpecHelpers.testTopicID + '/no_such_team', {trigger: true});
                AjaxHelpers.expectRequest(requests, 'GET', '/api/team/v0/teams/no_such_team?expand=user', null);
                AjaxHelpers.respondWithError(requests, 404);
                expectError(teamsTabView, 'The team "no_such_team" could not be found.');
                expectFocus(teamsTabView.$('.warning'));
            });

            it('displays and focuses an error message when it receives a 401 AJAX response', function() {
                var teamsTabView = createTeamsTabView().render();
                teamsTabView.router.navigate('topics/' + TeamSpecHelpers.testTopicID, {trigger: true});
                AjaxHelpers.respondWithError(requests, 401);
                expectError(teamsTabView, 'Your request could not be completed. Reload the page and try again.');
                expectFocus(teamsTabView.$('.warning'));
            });

            it('displays and focuses an error message when it receives a 500 AJAX response', function() {
                var teamsTabView = createTeamsTabView().render();
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
                var teamsTabView = createTeamsTabView(),
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
                    'teams/' + TeamSpecHelpers.testTopicID + '/test_team_id/edit-team',
                    {
                        page_name: 'edit-team',
                        topic_id: TeamSpecHelpers.testTopicID,
                        team_id: 'test_team_id'
                    }
                ]
            }, function(url, expectedEvent) {
                var teamsTabView = createTeamsTabView({
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
                var teamsTabView = createTeamsTabView({
                    userInfo: TeamSpecHelpers.createMockUserInfo({privileged: true})
                });
                // Note: using `undefined` here to ensure that we
                // don't even look at the team when the user is
                // privileged
                expect(teamsTabView.readOnlyDiscussion(undefined)).toBe(false);
            });

            it('allows access to a team which an unprivileged user is a member of', function() {
                var teamsTabView = createTeamsTabView({
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
                var teamsTabView = createTeamsTabView({
                    userInfo: TeamSpecHelpers.createMockUserInfo({privileged: false, staff: true})
                });
                expect(teamsTabView.readOnlyDiscussion({
                    attributes: {membership: []}
                })).toBe(true);
            });
        });

        describe('Manage Tab', function() {
            var manageTabSelector = '.page-content-nav>.nav-item[data-url=manage]';
            it('is not visible to unprivileged users', function() {
                var teamsTabView = createTeamsTabView({
                    userInfo: TeamSpecHelpers.createMockUserInfo({privileged: false}),
                    hasManagedTopic: true
                });
                expect(teamsTabView.$(manageTabSelector).length).toBe(0);
            });

            it('is not visible when there are no managed topics', function() {
                var teamsTabView = createTeamsTabView({
                    userInfo: TeamSpecHelpers.createMockUserInfo({privileged: true}),
                    hasManagedTopic: false
                });
                expect(teamsTabView.$(manageTabSelector).length).toBe(0);
            });

            it('is visible to privileged users when there is a managed topic', function() {
                var teamsTabView = createTeamsTabView({
                    userInfo: TeamSpecHelpers.createMockUserInfo({privileged: true}),
                    hasManagedTopic: true
                });
                expect(teamsTabView.$(manageTabSelector).length).toBe(1);
            });
        });

        describe('Browse Tab', function() {
            var browseTabSelector = '.page-content-nav>.nav-item[data-url=browse]';
            it('is not visible if there are no open and no public teamsets', function() {
                var teamsTabView = createTeamsTabView({
                    hasOpenTopic: false,
                    hasPublicManagedTopic: false
                });
                expect(teamsTabView.$(browseTabSelector).length).toBe(0);
            });

            it('is visible if there are open teamsets', function() {
                var teamsTabView = createTeamsTabView({
                    hasOpenTopic: true,
                    hasPublicManagedTopic: false
                });
                expect(teamsTabView.$(browseTabSelector).length).toBe(1);
            });

            it('is visible if there are public teamsets', function() {
                var teamsTabView = createTeamsTabView({
                    hasOpenTopic: false,
                    hasPublicManagedTopic: true
                });
                expect(teamsTabView.$(browseTabSelector).length).toBe(1);
            });

            it('is visible if there are both public and open teamsets', function() {
                var teamsTabView = createTeamsTabView({
                    hasOpenTopic: true,
                    hasPublicManagedTopic: true
                });
                expect(teamsTabView.$(browseTabSelector).length).toBe(1);
            });
        });

        describe('Search', function() {
            var teamsTabView;

            var performSearch = function() {
                teamsTabView.$('.search-field').val('foo');
                teamsTabView.$('.action-search').click();
                verifyTeamsRequest({
                    order_by: '',
                    text_search: 'foo'
                });
                AjaxHelpers.respondWithJson(
                  requests,
                  TeamSpecHelpers.createMockTeamsResponse({ results: [] }
                  ));
                AjaxHelpers.respondWithJson(requests, { count: 0 });

                // Expect exactly one search request to be fired, and one request to see if the user is
                // in a team in the current teamset
                AjaxHelpers.expectNoRequests(requests);
            };

            var setUpTopicTab = function() {
                teamsTabView = createTeamsTabView();
                teamsTabView.browseTopic(TeamSpecHelpers.testTopicID);
                verifyTeamsRequest({
                    order_by: 'last_activity_at',
                    text_search: ''
                });
                AjaxHelpers.respondWithJson(requests, {});
                AjaxHelpers.respondWithJson(requests, { count: 0 });
            };

            it('can search teams', function() {
                setUpTopicTab();
                performSearch();
                expect(teamsTabView.$('.page-title').text()).toBe('Team Search');
                expect(teamsTabView.$('.page-description').text()).toBe('Showing results for "foo"');
            });

            it('can clear a search', function() {
                setUpTopicTab();
                // Perform a search
                performSearch();

                // Clear the search and submit it again
                teamsTabView.$('.search-field').val('');
                teamsTabView.$('.action-search').click();

                verifyTeamsRequest({ order_by: 'last_activity_at' });
                AjaxHelpers.respondWithJson(requests, {});
                AjaxHelpers.respondWithJson(requests, { count: 0 });
                expect(teamsTabView.$('.page-title').text()).toBe('Test Topic 1');
                expect(teamsTabView.$('.page-description').text()).toBe('Test description 1');
            });

            it('updates the description when search string updates', function() {
                var newString = 'bar';
                setUpTopicTab();
                performSearch();
                expect(teamsTabView.$('.page-title').text()).toBe('Team Search');
                expect(teamsTabView.$('.page-description').text()).toBe('Showing results for "foo"');
                teamsTabView.$('.search-field').val(newString);
                teamsTabView.$('.action-search').click();
                AjaxHelpers.respondWithJson(requests, { count: 0 });
                expect(teamsTabView.$('.page-title').text()).toBe('Team Search');
                expect(teamsTabView.$('.page-description').text()).toBe(
                  'Showing results for "' + newString + '"'
                );
            });

            it('can navigate back to all teams from a search', function() {
                setUpTopicTab();
                // Perform a search
                performSearch();

                // Verify the breadcrumbs have a link back to the teams list, and click on it
                expect(teamsTabView.$('.breadcrumbs a').length).toBe(2);
                teamsTabView.$('.breadcrumbs a').last().click();
                verifyTeamsRequest({
                    order_by: 'last_activity_at',
                    text_search: ''
                });
                AjaxHelpers.respondWithJson(requests, {});
                AjaxHelpers.respondWithJson(requests, { count: 0 });
                expect(teamsTabView.$('.page-title').text()).toBe('Test Topic 1');
                expect(teamsTabView.$('.page-description').text()).toBe('Test description 1');
            });

            it('does not switch to showing results when the search returns an error', function() {
                setUpTopicTab();
                // Perform a search but respond with a 500
                teamsTabView.$('.search-field').val('foo');
                teamsTabView.$('.action-search').click();
                AjaxHelpers.respondWithError(requests);

                // Verify that the team list is still shown
                expect(teamsTabView.$('.page-title').text()).toBe('Test Topic 1');
                expect(teamsTabView.$('.page-description').text()).toBe('Test description 1');
                expect(teamsTabView.$('.search-field').val(), 'foo');
            });

            it('shows a search box in non-private team-sets', function() {
                setUpTopicTab();
                expect(teamsTabView.$('.search-field')).toExist();
            });

            it('does not show a search box in private team-sets for non-privileged users', function() {
                teamsTabView = createTeamsTabView({
                    topics: {
                        results: TeamSpecHelpers.createMockTopic({type: 'private_managed'})
                    }
                });

                teamsTabView.browseTopic(TeamSpecHelpers.testTopicID);

                verifyTeamsRequest({
                    order_by: 'last_activity_at',
                    text_search: ''
                });
                AjaxHelpers.respondWithJson(requests, {});

                expect(teamsTabView.$('.search-field')).not.toExist();
            });

            it('shows a search box in private team-sets for privileged users', function() {
                teamsTabView = createTeamsTabView({
                    topics: {
                        results: TeamSpecHelpers.createMockTopic({type: 'private_managed'})
                    },
                    userInfo: TeamSpecHelpers.createMockUserInfo({
                        privileged: true,
                        staff: true
                    })
                });

                teamsTabView.browseTopic(TeamSpecHelpers.testTopicID);

                verifyTeamsRequest({
                    order_by: 'last_activity_at',
                    text_search: ''
                });
                AjaxHelpers.respondWithJson(requests, {});

                expect(teamsTabView.$('.search-field')).toExist();
            });
        });
    });
});
