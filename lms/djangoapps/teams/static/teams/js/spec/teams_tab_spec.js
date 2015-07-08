define([
    'jquery',
    'backbone',
    'common/js/spec_helpers/ajax_helpers',
    'teams/js/views/teams_tab'
], function ($, Backbone, AjaxHelpers, TeamsTabView) {
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
                        id: 'test_id',
                        team_count: 0
                    }]
                },
                topic_url: 'api/topics/topic_id,course_id',
                topics_url: 'topics_url',
                teams_url: 'teams_url',
                course_id: 'test/course/id'
            }).render();
            Backbone.history.start();
        });

        afterEach(function () {
            Backbone.history.stop();
        });

        it('shows the teams tab initially', function () {
            expectHeader('See all teams in your course, organized by topic');
            expectContent('This is the new Teams tab.');
        });

        it('can switch tabs', function () {
            teamsTabView.$('a.nav-item[data-url="browse"]').click();
            expectContent('test description');
            teamsTabView.$('a.nav-item[data-url="teams"]').click();
            expectContent('This is the new Teams tab.');
        });

        it('displays an error message when trying to navigate to a nonexistent route', function () {
            teamsTabView.router.navigate('test', {trigger: true});
            expectError('The page "test" could not be found.');
        });

        it('displays an error message when trying to navigate to a nonexistent topic', function () {
            var requests = AjaxHelpers.requests(this);
            teamsTabView.router.navigate('topics/test', {trigger: true});
            AjaxHelpers.expectRequest(requests, 'GET', 'api/topics/test,course_id', null);
            AjaxHelpers.respondWithError(requests, 404);
            expectError('The topic "test" could not be found.');
        });
    });
});
