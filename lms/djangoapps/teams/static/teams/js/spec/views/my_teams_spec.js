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
            return new MyTeamsView(_.extend(
                {
                    el: '.teams-container',
                    collection: options.teams || TeamSpecHelpers.createMockTeams(),
                    teamMemberships: TeamSpecHelpers.createMockTeamMemberships(),
                    showActions: true,
                    context: TeamSpecHelpers.testContext
                },
                options
            )).render();
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
            AjaxHelpers.expectRequestURL(
                requests,
                TeamSpecHelpers.testContext.teamMembershipsUrl,
                {
                    expand : 'team',
                    username : TeamSpecHelpers.testContext.userInfo.username,
                    course_id : TeamSpecHelpers.testContext.courseID,
                    page : '1',
                    page_size : '10',
                    text_search: ''
                }
            );
            AjaxHelpers.respondWithJson(requests, {});
        });
    });
});
