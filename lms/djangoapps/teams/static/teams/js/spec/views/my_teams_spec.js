define([
    'backbone',
    'teams/js/collections/team',
    'teams/js/collections/team_membership',
    'teams/js/views/my_teams',
    'teams/js/spec_helpers/team_spec_helpers'
], function (Backbone, TeamCollection, TeamMembershipCollection, MyTeamsView, TeamSpecHelpers) {
    'use strict';
    describe('My Teams View', function () {
        beforeEach(function () {
            setFixtures('<div class="teams-container"></div>');
        });

        var createMyTeamsView = function(options) {
            return new MyTeamsView({
                el: '.teams-container',
                collection: options.teams || TeamSpecHelpers.createMockTeams(),
                teamMemberships: options.teamMemberships || TeamSpecHelpers.createMockTeamMemberships(),
                showActions: true,
                teamParams: {
                    topicID: 'test-topic',
                    countries: TeamSpecHelpers.testCountries,
                    languages: TeamSpecHelpers.testLanguages
                }
            }).render();
        };

        it('can render itself', function () {
            var teamMembershipsData = TeamSpecHelpers.createMockTeamMembershipsData(1, 5),
                teamMemberships = TeamSpecHelpers.createMockTeamMemberships(teamMembershipsData),
                teamsView = createMyTeamsView({
                    teams: teamMemberships,
                    teamMemberships: teamMemberships
                });

            TeamSpecHelpers.verifyCards(teamsView, teamMembershipsData);

            // Verify that there is no header or footer
            expect(teamsView.$('.teams-paging-header').text().trim()).toBe('');
            expect(teamsView.$('.teams-paging-footer').text().trim()).toBe('');
        });

        it('shows a message when the user is not a member of any teams', function () {
            var teamMemberships = TeamSpecHelpers.createMockTeamMemberships([]),
                teamsView = createMyTeamsView({
                    teams: teamMemberships,
                    teamMemberships: teamMemberships
                });
            TeamSpecHelpers.verifyCards(teamsView, []);
            expect(teamsView.$el.text().trim()).toBe('You are not currently a member of any teams.');
        });
    });
});
