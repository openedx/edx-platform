define([
    'jquery',
    'backbone',
    'common/js/spec_helpers/ajax_helpers',
    'teams/js/views/teams_tab',
    'URI'
], function ($, Backbone, AjaxHelpers, TeamsTabView, URI) {
    'use strict';

    describe('TeamsTab', function () {
        var teamsTabView,
            expectContent = function (text) {
                expect(teamsTabView.$('.page-content-main').text()).toContain(text);
            },
            expectHeader = function (text) {
                expect(teamsTabView.$('.teams-header').text()).toContain(text);
            },
            expectError = function (text) {
                expect(teamsTabView.$('.warning').text()).toContain(text);
            },
            expectFocus = function (element) {
                expect(element.focus).toHaveBeenCalled();
            };

        beforeEach(function () {
            setFixtures('<div class="teams-content"></div>');
            teamsTabView = new TeamsTabView({
                el: $('.teams-content'),
                topics: {
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
                topicsUrl: 'api/topics/',
                topicUrl: 'api/topics/topic_id,test/course/id',
                teamsUrl: 'api/teams/',
                courseID: 'test/course/id'
            }).render();
            Backbone.history.start();
            spyOn($.fn, 'focus');
        });

        afterEach(function () {
            Backbone.history.stop();
        });

        it('shows the teams tab initially', function () {
            expectHeader('See all teams in your course, organized by topic');
            expectContent('This is the new Teams tab.');
        });

        describe('Navigation', function () {
            it('can switch tabs', function () {
                teamsTabView.$('a.nav-item[data-url="browse"]').click();
                expectContent('test description');
                teamsTabView.$('a.nav-item[data-url="teams"]').click();
                expectContent('This is the new Teams tab.');
            });

            it('displays and focuses an error message when trying to navigate to a nonexistent page', function () {
                teamsTabView.router.navigate('no_such_page', {trigger: true});
                expectError('The page "no_such_page" could not be found.');
                expectFocus(teamsTabView.$('.warning'));
            });

            it('displays and focuses an error message when trying to navigate to a nonexistent topic', function () {
                var requests = AjaxHelpers.requests(this);
                teamsTabView.router.navigate('topics/no_such_topic', {trigger: true});
                AjaxHelpers.expectRequest(requests, 'GET', 'api/topics/no_such_topic,test/course/id', null);
                AjaxHelpers.respondWithError(requests, 404);
                expectError('The topic "no_such_topic" could not be found.');
                expectFocus(teamsTabView.$('.warning'));
            });

            it('displays and focuses an error message when trying to navigate to a nonexistent team', function () {
                var requests = AjaxHelpers.requests(this);
                teamsTabView.router.navigate('teams/test_topic/no_such_team', {trigger: true});
                AjaxHelpers.expectRequest(requests, 'GET', 'api/teams/no_such_team', null);
                AjaxHelpers.respondWithError(requests, 404);
                expectError('The team "no_such_team" could not be found.');
                expectFocus(teamsTabView.$('.warning'));
            });
        });
    });
});
