define([
    'backbone',
    'underscore',
    'teams/js/views/topic_teams',
    'teams/js/spec_helpers/team_spec_helpers',
    'common/js/spec_helpers/page_helpers'
], function(Backbone, _, TopicTeamsView, TeamSpecHelpers, PageHelpers) {
    'use strict';
    describe('Topic Teams View', function() {
        var createTopicTeamsView = function(options, isInstructorManagedTopic) {
            var myTeamsCollection;
            options = options || {}; // eslint-disable-line no-param-reassign
            myTeamsCollection = options.myTeamsCollection || TeamSpecHelpers.createMockTeams({results: []});
            return new TopicTeamsView({
                el: '.teams-container',
                model: isInstructorManagedTopic ?
                    TeamSpecHelpers.createMockInstructorManagedTopic() : TeamSpecHelpers.createMockTopic(),
                collection: options.teams || TeamSpecHelpers.createMockTeams(),
                myTeamsCollection: myTeamsCollection,
                showActions: true,
                context: _.extend({}, TeamSpecHelpers.testContext, options)
            }).render();
        };

        var verifyActions = function(teamsView, options) {
            var expectedTitle = 'Are you having trouble finding a team to join?',
                expectedMessage = 'Browse teams in other topics or search teams in this topic. ' +
                    'If you still can\'t find a team to join, create a new team in this topic.',
                title = teamsView.$('.title').text().trim(),
                message = teamsView.$('.copy').text().trim();
            if (!options) {
                options = {showActions: true}; // eslint-disable-line no-param-reassign
            }

            if (options.showActions) {
                expect(title).toBe(expectedTitle);
                expect(message).toBe(expectedMessage);
            } else {
                expect(title).not.toBe(expectedTitle);
                expect(message).not.toBe(expectedMessage);
            }
        };

        beforeEach(function() {
            setFixtures('<div class="teams-container"></div>');
            PageHelpers.preventBackboneChangingUrl();
        });

        it('can render itself', function() {
            var testTeamData = TeamSpecHelpers.createMockTeamData(1, 5),
                teamsView = createTopicTeamsView({
                    teams: TeamSpecHelpers.createMockTeams({
                        results: testTeamData
                    })
                });
            var footerEl = teamsView.$('.teams-paging-footer');
            expect(teamsView.$('.teams-paging-header').text()).toMatch('Showing 1-5 out of 6 total');
            expect(footerEl.text()).toMatch('1\\s+out of\\s+\/\\s+2'); // eslint-disable-line no-useless-escape
            expect(footerEl).not.toHaveClass('hidden');

            TeamSpecHelpers.verifyCards(teamsView, testTeamData);
            verifyActions(teamsView);
        });

        it('can browse all teams', function() {
            var teamsView = createTopicTeamsView();
            spyOn(Backbone.history, 'navigate');
            teamsView.$('.browse-teams').click();
            expect(Backbone.history.navigate.calls.mostRecent().args[0]).toBe('browse');
        });

        it('gives the search field focus when clicking on the search teams link', function() {
            var teamsView = createTopicTeamsView();
            spyOn($.fn, 'focus').and.callThrough();
            teamsView.$('.search-teams').click();
            expect(teamsView.$('.search-field').first().focus).toHaveBeenCalled();
        });

        it('can show the create team modal', function() {
            var teamsView = createTopicTeamsView();
            spyOn(Backbone.history, 'navigate');
            teamsView.$('a.create-team').click();
            expect(Backbone.history.navigate.calls.mostRecent().args[0]).toBe(
                'topics/' + TeamSpecHelpers.testTopicID + '/create-team'
            );
        });

        it('does not show actions for a user already in a team', function() {
            var options = {myTeamsCollection: TeamSpecHelpers.createMockTeams()};
            var teamsView = createTopicTeamsView(options);
            verifyActions(teamsView, {showActions: false});
        });

        it('does not show actions for a student in an instructor managed topic', function() {
            var teamsView = createTopicTeamsView({}, true);
            verifyActions(teamsView, {showActions: false});
        });

        it('shows actions for a privileged user already in a team', function() {
            var options = {
                userInfo: {
                    privileged: true,
                    staff: false
                },
                myTeamsCollection: TeamSpecHelpers.createMockTeams()
            };
            var teamsView = createTopicTeamsView(options);
            verifyActions(teamsView, {showActions: true});
        });

        it('shows actions for a staff user already in a team', function() {
            var options = {
                userInfo: {
                    privileged: false,
                    staff: true
                },
                myTeamsCollection: TeamSpecHelpers.createMockTeams()
            };
            var teamsView = createTopicTeamsView(options);
            verifyActions(teamsView, {showActions: true});
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
