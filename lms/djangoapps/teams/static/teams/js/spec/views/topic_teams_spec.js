define([
    'backbone',
    'underscore',
    'teams/js/views/topic_teams',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
    'teams/js/spec_helpers/team_spec_helpers',
    'common/js/spec_helpers/page_helpers'
], function(Backbone, _, TopicTeamsView, AjaxHelpers, TeamSpecHelpers, PageHelpers) {
    'use strict';
    describe('Topic Teams View', function() {
        var requests, teamsView;

        var verifyTeamsetTeamsRequest = function(hasTeams) {
            AjaxHelpers.expectRequestURL(
                requests,
                TeamSpecHelpers.testContext.teamMembershipsUrl,
                {
                    username: TeamSpecHelpers.testUser,
                    course_id: TeamSpecHelpers.testCourseID,
                    teamset_id: TeamSpecHelpers.testTopicID,
                }
            );
            AjaxHelpers.respondWithJson(
                requests,
                { count: hasTeams ? 1 : 0 }
            );
            AjaxHelpers.expectNoRequests(requests);
        };

        var createTopicTeamsView = function(_options) {
            var options = _options || {};
            var onTeamInTeamset = options.onTeamInTeamset || false,
                isInstructorManagedTopic = options.isInstructorManagedTopic || false;

            var result, topicTeamsView;

            requests = AjaxHelpers.requests(this);
            topicTeamsView = new TopicTeamsView({
                el: '.teams-container',
                model: isInstructorManagedTopic ?
                    TeamSpecHelpers.createMockTopic({type: 'public_managed'}) : TeamSpecHelpers.createMockTopic(),
                collection: options.teams || TeamSpecHelpers.createMockTeams({results: []}),
                context: _.extend({}, TeamSpecHelpers.testContext, options)
            });
            result = topicTeamsView.render();

            if (
                topicTeamsView.context.userInfo.staff ||
                topicTeamsView.context.userInfo.privileged ||
                isInstructorManagedTopic
            ) {
                AjaxHelpers.expectNoRequests(requests);
            } else {
                verifyTeamsetTeamsRequest(onTeamInTeamset);
            }
            return result;
        };

        var verifyActions = function(showActions) {
            var expectedTitle = 'Are you having trouble finding a team to join?',
                expectedMessage = 'Browse teams in other topics or search teams in this topic. ' +
                    'If you still can\'t find a team to join, create a new team in this topic.',
                title = teamsView.$('.title').text().trim(),
                message = teamsView.$('.copy').text().trim(),
                _showActions = showActions === undefined ? true : showActions;

            if (_showActions) {
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
            var testTeamData = TeamSpecHelpers.createMockTeamData(1, 5);
            var options = {
                teams: TeamSpecHelpers.createMockTeams({
                    results: testTeamData
                })
            };
            var footerEl;

            teamsView = createTopicTeamsView(options);
            footerEl = teamsView.$('.teams-paging-footer');

            expect(teamsView.$('.teams-paging-header').text()).toMatch('Showing 1-5 out of 6 total');
            expect(footerEl.text()).toMatch('1\\s+out of\\s+\/\\s+2'); // eslint-disable-line no-useless-escape
            expect(footerEl).not.toHaveClass('hidden');

            TeamSpecHelpers.verifyCards(teamsView, testTeamData);
            verifyActions();
        });

        it('can browse all teams', function() {
            teamsView = createTopicTeamsView();
            spyOn(Backbone.history, 'navigate');
            teamsView.$('.browse-teams').click();
            expect(Backbone.history.navigate.calls.mostRecent().args[0]).toBe('browse');
        });

        it('gives the search field focus when clicking on the search teams link', function() {
            teamsView = createTopicTeamsView();
            spyOn($.fn, 'focus').and.callThrough();
            teamsView.$('.search-teams').click();
            expect(teamsView.$('.search-field').first().focus).toHaveBeenCalled();
        });

        it('can show the create team modal', function() {
            teamsView = createTopicTeamsView();
            spyOn(Backbone.history, 'navigate');
            teamsView.$('a.create-team').click();
            expect(Backbone.history.navigate.calls.mostRecent().args[0]).toBe(
                'topics/' + TeamSpecHelpers.testTopicID + '/create-team'
            );
        });

        it('does not show actions for a user already in a team in the teamset', function() {
            teamsView = createTopicTeamsView({ onTeamInTeamset: true });
            verifyActions(false);
        });

        it('does not show actions for a student in an instructor managed topic', function() {
            teamsView = createTopicTeamsView({ isInstructorManagedTopic: true });
            verifyActions(false);
        });

        it('shows actions for a privileged user already in a team', function() {
            var options = {
                userInfo: {
                    privileged: true,
                    staff: false
                },
                onTeamInTeamset: true,
            };
            teamsView = createTopicTeamsView(options);
            verifyActions();
        });

        it('shows actions for a staff user already in a team', function() {
            var options = {
                userInfo: {
                    privileged: false,
                    staff: true
                },
                onTeamInTeamset: true,
            };
            teamsView = createTopicTeamsView(options);
            verifyActions();
        });

        /*
        // TODO: make this ready for prime time
        it('refreshes when the team membership changes', function() {
            var requests = AjaxHelpers.requests(this),
                teamMemberships = TeamSpecHelpers.createMockTeamMemberships([]),
                teamsView = createTopicTeamsView({ teamMemberships: teamMemberships });
            verifyActions({showActions: true});
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
            verifyActions({showActions: false});
        });
        */
    });
});
