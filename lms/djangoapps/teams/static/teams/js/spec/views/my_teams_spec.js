define([
    'backbone',
    'teams/js/collections/team',
    'teams/js/collections/team_membership',
    'teams/js/views/my_teams',
    'teams/js/spec_helpers/team_spec_helpers',
    'common/js/spec_helpers/ajax_helpers'
], function (Backbone, TeamCollection, TeamMembershipCollection, MyTeamsView, TeamSpecHelpers, AjaxHelpers) {
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
                myTeamsView = createMyTeamsView({
                    teams: teamMemberships,
                    teamMemberships: teamMemberships
                });

            TeamSpecHelpers.verifyCards(myTeamsView, teamMembershipsData);

            // Verify that there is no header or footer
            expect(myTeamsView.$('.teams-paging-header').text().trim()).toBe('');
            expect(myTeamsView.$('.teams-paging-footer').text().trim()).toBe('');
        });

        it('shows a message when the user is not a member of any teams', function () {
            var teamMemberships = TeamSpecHelpers.createMockTeamMemberships([]),
                myTeamsView = createMyTeamsView({
                    teams: teamMemberships,
                    teamMemberships: teamMemberships
                });
            TeamSpecHelpers.verifyCards(myTeamsView, []);
            expect(myTeamsView.$el.text().trim()).toBe('You are not currently a member of any team.');
        });

        it('refreshes a stale membership collection when rendering', function() {
            var requests = AjaxHelpers.requests(this),
                teamMemberships = TeamSpecHelpers.createMockTeamMemberships([]),
                myTeamsView = createMyTeamsView({
                    teams: teamMemberships,
                    teamMemberships: teamMemberships
                });
            TeamSpecHelpers.verifyCards(myTeamsView, []);
            expect(myTeamsView.$el.text().trim()).toBe('You are not currently a member of any team.');
            teamMemberships.teamEvents.trigger('teams:update', { action: 'create' });
            myTeamsView.render();
            AjaxHelpers.expectJsonRequestURL(
                requests,
                'foo',
                {
                    expand : 'team',
                    username : 'testUser',
                    course_id : 'my/course/id',
                    page : '1',
                    page_size : '10'
                }
            );
            AjaxHelpers.respondWithJson(requests, {});
        });
    });
});
