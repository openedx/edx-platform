define([
    'backbone',
    'teams/js/collections/team',
    'teams/js/collections/team_membership',
    'teams/js/views/topic_teams',
    'teams/js/spec_helpers/team_spec_helpers'
], function (Backbone, TeamCollection, TeamMembershipCollection, TopicTeamsView, TeamSpecHelpers) {
    'use strict';
    describe('Topic Teams View', function () {
        var createTopicTeamsView = function(options) {
            return new TopicTeamsView({
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

        beforeEach(function () {
            setFixtures('<div class="teams-container"></div>');
        });

        it('can render itself', function () {
            var testTeamData = TeamSpecHelpers.createMockTeamData(1, 5),
                teamsView = createTopicTeamsView({
                    teams: TeamSpecHelpers.createMockTeams(testTeamData),
                    teamMemberships: TeamSpecHelpers.createMockTeamMemberships([])
                });

            expect(teamsView.$('.teams-paging-header').text()).toMatch('Showing 1-5 out of 6 total');

            var footerEl = teamsView.$('.teams-paging-footer');
            expect(footerEl.text()).toMatch('1\\s+out of\\s+\/\\s+2');
            expect(footerEl).not.toHaveClass('hidden');

            TeamSpecHelpers.verifyCards(teamsView, testTeamData);

            expect(teamsView.$('.title').text()).toBe('Are you having trouble finding a team to join?');
            expect(teamsView.$('.copy').text()).toBe(
                "Try browsing all teams or searching team descriptions. If you " +
                "still can't find a team to join, create a new team in this topic."
            );
        });

        it('can browse all teams', function () {
            var emptyMembership = TeamSpecHelpers.createMockTeamMemberships([]),
                teamsView = createTopicTeamsView({ teamMemberships: emptyMembership });
            spyOn(Backbone.history, 'navigate');
            teamsView.$('a.browse-teams').click();
            expect(Backbone.history.navigate.calls[0].args).toContain('browse');
        });

        it('can search teams', function () {
            var emptyMembership = TeamSpecHelpers.createMockTeamMemberships([]),
                teamsView = createTopicTeamsView({ teamMemberships: emptyMembership });
            spyOn(Backbone.history, 'navigate');
            teamsView.$('a.search-teams').click();
            // TODO! Should be updated once team description search feature is available
            expect(Backbone.history.navigate.calls[0].args).toContain('browse');
        });

        it('can show the create team modal', function () {
            var emptyMembership = TeamSpecHelpers.createMockTeamMemberships([]),
                teamsView = createTopicTeamsView({ teamMemberships: emptyMembership });
            spyOn(Backbone.history, 'navigate');
            teamsView.$('a.create-team').click();
            expect(Backbone.history.navigate.calls[0].args).toContain('topics/test-topic/create-team');
        });

        it('does not show actions for a user already in a team', function () {
            var teamsView = createTopicTeamsView({});
            expect(teamsView.$el.text()).not.toContain(
                'Are you having trouble finding a team to join?'
            );
        });

        it('shows actions for a privileged user already in a team', function () {
            var staffMembership = TeamSpecHelpers.createMockTeamMemberships(
                    TeamSpecHelpers.createMockTeamMembershipsData(1, 5),
                    { privileged: true }
                ),
                teamsView = createTopicTeamsView({ teamMemberships: staffMembership });
            expect(teamsView.$el.text()).toContain(
                'Are you having trouble finding a team to join?'
            );
        });
    });
});
