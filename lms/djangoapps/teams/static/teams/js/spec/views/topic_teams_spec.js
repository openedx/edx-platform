define([
    'backbone',
    'underscore',
    'teams/js/views/topic_teams',
    'teams/js/spec_helpers/team_spec_helpers',
    'common/js/spec_helpers/page_helpers'
], function (Backbone, _, TopicTeamsView, TeamSpecHelpers, PageHelpers) {
    'use strict';
    describe('Topic Teams View', function () {
        var createTopicTeamsView = function(options) {
            options = options || {};
            var myTeamsCollection = options.myTeamsCollection || TeamSpecHelpers.createMockTeams({results: []});
            return new TopicTeamsView({
                el: '.teams-container',
                model: TeamSpecHelpers.createMockTopic(),
                collection: options.teams || TeamSpecHelpers.createMockTeams(),
                myTeamsCollection: myTeamsCollection,
                showActions: true,
                context: _.extend({}, TeamSpecHelpers.testContext, options)
            }).render();
        };

        var verifyActions = function(teamsView, options) {
            if (!options) {
                options = {showActions: true};
            }
            var expectedTitle = 'Are you having trouble finding a team to join?',
                expectedMessage = 'Browse teams in other topics or search teams in this topic. ' +
                    'If you still can\'t find a team to join, create a new team in this topic.',
                title = teamsView.$('.title').text().trim(),
                message = teamsView.$('.copy').text().trim();
            if (options.showActions) {
                expect(title).toBe(expectedTitle);
                expect(message).toBe(expectedMessage);
            } else {
                expect(title).not.toBe(expectedTitle);
                expect(message).not.toBe(expectedMessage);
            }
        };

        beforeEach(function () {
            setFixtures('<div class="teams-container"></div>');
            PageHelpers.preventBackboneChangingUrl();
        });

        it('can render itself', function () {
            var testTeamData = TeamSpecHelpers.createMockTeamData(1, 5),
                teamsView = createTopicTeamsView({
                    teams: TeamSpecHelpers.createMockTeams({
                        results: testTeamData
                    })
                });

            expect(teamsView.$('.teams-paging-header').text()).toMatch('Showing 1-5 out of 6 total');

            var footerEl = teamsView.$('.teams-paging-footer');
            expect(footerEl.text()).toMatch('1\\s+out of\\s+\/\\s+2');
            expect(footerEl).not.toHaveClass('hidden');

            TeamSpecHelpers.verifyCards(teamsView, testTeamData);
            verifyActions(teamsView);
        });

        it('can browse all teams', function () {
            var teamsView = createTopicTeamsView();
            spyOn(Backbone.history, 'navigate');
            teamsView.$('.browse-teams').click();
            expect(Backbone.history.navigate.calls.mostRecent().args[0]).toBe('browse');
        });

        it('gives the search field focus when clicking on the search teams link', function () {
            var teamsView = createTopicTeamsView();
            spyOn($.fn, 'focus').and.callThrough();
            teamsView.$('.search-teams').click();
            expect(teamsView.$('.search-field').first().focus).toHaveBeenCalled();
        });

        it('can show the create team modal', function () {
            var teamsView = createTopicTeamsView();
            spyOn(Backbone.history, 'navigate');
            teamsView.$('a.create-team').click();
            expect(Backbone.history.navigate.calls.mostRecent().args[0]).toBe(
                'topics/' + TeamSpecHelpers.testTopicID + '/create-team'
            );
        });

        it('does not show actions for a user already in a team', function () {
            var teamsView = createTopicTeamsView({myTeamsCollection: TeamSpecHelpers.createMockTeams()});
            verifyActions(teamsView, {showActions: false});
        });

        it('shows actions for a privileged user already in a team', function () {
            var teamsView = createTopicTeamsView({ privileged: true });
            verifyActions(teamsView);
        });

        it('shows actions for a staff user already in a team', function () {
            var teamsView = createTopicTeamsView({ privileged: false, staff: true });
            verifyActions(teamsView);
        });

        /*
        // TODO: make this ready for prime time
        it('refreshes when the team membership changes', function() {
            var requests = AjaxHelpers.requests(this),
                teamMemberships = TeamSpecHelpers.createMockTeamMemberships([]),
                teamsView = createTopicTeamsView({ teamMemberships: teamMemberships });
            verifyActions(teamsView, {showActions: true});
            teamMemberships.teamEvents.trigger('teams:update', { action: 'create' });
            teamsView.render();
            AjaxHelpers.expectRequestURL(
                requests,
                'foo',
                {
                    expand : 'team',
                    username : 'testUser',
                    course_id : TeamSpecHelpers.testCourseID,
                    page : '1',
                    page_size : '10'
                }
            );
            AjaxHelpers.respondWithJson(requests, {});
            verifyActions(teamsView, {showActions: false});
        });
        */
    });
});
