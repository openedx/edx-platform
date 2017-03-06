define([
    'backbone',
    'teams/js/collections/my_teams',
    'teams/js/views/my_teams',
    'teams/js/spec_helpers/team_spec_helpers',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers'
], function (Backbone, MyTeamsCollection, MyTeamsView, TeamSpecHelpers, AjaxHelpers) {
    'use strict';
    describe('My Teams View', function () {
        beforeEach(function () {
            setFixtures('<div class="teams-container"></div>');
        });

        var createMyTeamsView = function(myTeams) {
            return new MyTeamsView({
                el: '.teams-container',
                collection: myTeams,
                showActions: true,
                context: TeamSpecHelpers.testContext
            }).render();
        };

        it('can render itself', function () {
            var teamsData = TeamSpecHelpers.createMockTeamData(1, 5),
                teams = TeamSpecHelpers.createMockTeams({results: teamsData}),
                myTeamsView = createMyTeamsView(teams);
            TeamSpecHelpers.verifyCards(myTeamsView, teamsData);

            // Verify that there is no header or footer
            expect(myTeamsView.$('.teams-paging-header').text().trim()).toBe('');
            expect(myTeamsView.$('.teams-paging-footer').text().trim()).toBe('');
        });

        it('shows a message when the user is not a member of any teams', function () {
            var teams = TeamSpecHelpers.createMockTeams({results: []}),
                myTeamsView = createMyTeamsView(teams);
            TeamSpecHelpers.verifyCards(myTeamsView, []);
            expect(myTeamsView.$el.text().trim()).toBe('You are not currently a member of any team.');
        });

        it('refreshes a stale membership collection when rendering', function() {
            var requests = AjaxHelpers.requests(this),
                teams = TeamSpecHelpers.createMockTeams({
                    results: []
                }, {
                    url: TeamSpecHelpers.testContext.myTeamsUrl,
                    username: TeamSpecHelpers.testContext.userInfo.username
                }, MyTeamsCollection),
                myTeamsView = createMyTeamsView(teams);
            TeamSpecHelpers.verifyCards(myTeamsView, []);
            expect(myTeamsView.$el.text().trim()).toBe('You are not currently a member of any team.');
            TeamSpecHelpers.teamEvents.trigger('teams:update', { action: 'create' });
            myTeamsView.render();
            AjaxHelpers.expectRequestURL(
                requests,
                TeamSpecHelpers.testContext.myTeamsUrl,
                {
                    expand : 'user',
                    username : TeamSpecHelpers.testContext.userInfo.username,
                    course_id : TeamSpecHelpers.testContext.courseID,
                    page : '1',
                    page_size : '5',
                    text_search: '',
                    order_by: 'last_activity_at'
                }
            );
            AjaxHelpers.respondWithJson(requests, {});
        });
    });
});
