define([
    'backbone',
    'teams/js/collections/team',
    'teams/js/views/teams',
    'teams/js/spec_helpers/team_spec_helpers'
], function (Backbone, TeamCollection, TeamsView, TeamSpecHelpers) {
    'use strict';
    describe('Teams View', function () {
        beforeEach(function () {
            setFixtures('<div class="teams-container"></div>');
        });

        var createTeamsView = function(options) {
            return new TeamsView({
                el: '.teams-container',
                collection: options.teams || TeamSpecHelpers.createMockTeams(),
                showActions: true,
                context: TeamSpecHelpers.testContext
            }).render();
        };

        it('can render itself', function () {
            var testTeamData = TeamSpecHelpers.createMockTeamData(1, 5),
                teamsView = createTeamsView({
                    teams: TeamSpecHelpers.createMockTeams({
                        results: testTeamData
                    })
                });

            expect(teamsView.$('.teams-paging-header').text()).toMatch('Showing 1-5 out of 6 total');

            var footerEl = teamsView.$('.teams-paging-footer');
            expect(footerEl.text()).toMatch('1\\s+out of\\s+\/\\s+2');
            expect(footerEl).not.toHaveClass('hidden');

            TeamSpecHelpers.verifyCards(teamsView, testTeamData);
        });
    });
});
