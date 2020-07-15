define([
    'backbone', 'underscore', 'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers', 'teams/js/models/team',
    'teams/js/views/team_profile_header_actions', 'teams/js/spec_helpers/team_spec_helpers'
], function(Backbone, _, AjaxHelpers, TeamModel, TeamProfileHeaderActionsView, TeamSpecHelpers) {
    'use strict';

    describe('TeamProfileHeaderActionsView', function() {
        var createTeamsUrl,
            createTeamModelData,
            createMembershipData,
            createHeaderActionsView,
            verifyErrorMessage,
            ACCOUNTS_API_URL = '/api/user/v1/accounts/';

        createTeamsUrl = function(teamId) {
            return TeamSpecHelpers.testContext.teamsUrl + teamId + '?expand=user';
        };

        createTeamModelData = function(teamId, teamName, membership) {
            return {
                id: teamId,
                name: teamName,
                membership: membership,
                url: createTeamsUrl(teamId),
                topic_id: 'topic-id'
            };
        };

        createHeaderActionsView =
            function(
                requests,
                courseMaxTeamSize,
                currentUsername,
                teamModelData,
                showEditButton,
                isInstructorManagedTopic,
                topicMaxTeamSize
            ) {
                var model = new TeamModel(teamModelData, {parse: true}),
                    context = TeamSpecHelpers.createMockContext({
                        courseMaxTeamSize: courseMaxTeamSize,
                        userInfo: TeamSpecHelpers.createMockUserInfo({
                            username: currentUsername
                        })
                    }),
                    topicOptions = typeof topicMaxTeamSize !== 'undefined' ?
                        {max_team_size: topicMaxTeamSize} : {},
                    topic;

                topicOptions.type = isInstructorManagedTopic ? 'public_managed' : 'open';
                topic = TeamSpecHelpers.createMockTopic(topicOptions);

                return new TeamProfileHeaderActionsView(
                    {
                        courseID: TeamSpecHelpers.testCourseID,
                        teamEvents: TeamSpecHelpers.teamEvents,
                        context: context,
                        model: model,
                        topic: topic,
                        showEditButton: showEditButton
                    }
                ).render();
            };

        createMembershipData = function(username) {
            return [
                {
                    user: {
                        username: username,
                        url: ACCOUNTS_API_URL + username
                    }
                }
            ];
        };

        describe('JoinButton', function() {
            beforeEach(function() {
                setFixtures(
                    '<div class="teams-content">\n' +
                        '<div class="msg-content">\n' +
                            '<div class="copy"></div>\n' +
                        '</div>\n' +
                        '<div class="header-action-view"></div>\n' +
                    '</div>'
                );
            });

            verifyErrorMessage = function(requests, errorMessage, expectedMessage, joinTeam) {
                var view = createHeaderActionsView(requests, 1, 'ma', createTeamModelData('teamA', 'teamAlpha', []));
                if (joinTeam) {
                    // if we want the error to return when user try to join team, respond with no membership
                    AjaxHelpers.respondWithJson(requests, {count: 0});
                    view.$('.action.action-primary').click();
                }
                AjaxHelpers.respondWithTextError(requests, 400, errorMessage);
                expect($('.msg-content .copy').text().trim()).toBe(expectedMessage);
            };

            it('can render itself', function() {
                var requests = AjaxHelpers.requests(this);
                var teamModelData = createTeamModelData('teamA', 'teamAlpha', createMembershipData('ma'));
                var view = createHeaderActionsView(requests, 1, 'ma', teamModelData);

                expect(view.$('.join-team').length).toEqual(1);
            });

            it('can join team successfully', function() {
                var requests = AjaxHelpers.requests(this);
                var currentUsername = 'ma1';
                var teamId = 'teamA';
                var teamName = 'teamAlpha';
                var teamModelData = createTeamModelData(teamId, teamName, []);
                var view = createHeaderActionsView(requests, 1, currentUsername, teamModelData);

                // a get request will be sent to get user membership info
                // because current user is not member of current team
                AjaxHelpers.expectRequest(
                    requests,
                    'GET',
                    TeamSpecHelpers.testContext.teamMembershipsUrl + '?' + $.param({
                        username: currentUsername,
                        course_id: TeamSpecHelpers.testCourseID,
                        teamset_id: 'topic-id'
                    })
                );

                // current user is not a member of any team so we should see the Join Team button
                AjaxHelpers.respondWithJson(requests, {count: 0});
                expect(view.$('.action.action-primary').length).toEqual(1);

                // a post request will be sent to add current user to current team
                view.$('.action.action-primary').click();
                AjaxHelpers.expectRequest(
                    requests,
                    'POST',
                    TeamSpecHelpers.testContext.teamMembershipsUrl,
                    $.param({username: currentUsername, team_id: teamId})
                );
                AjaxHelpers.respondWithJson(requests, {});

                // on success, team model will be fetched and
                // join team view and team profile will be re-rendered
                AjaxHelpers.expectRequest(
                    requests,
                    'GET',
                    createTeamsUrl(teamId)
                );
                AjaxHelpers.respondWithJson(
                    requests, createTeamModelData(teamId, teamName, createMembershipData(currentUsername))
                );

                // current user is now member of the current team then there should be no button and no message
                expect(view.$('.action.action-primary').length).toEqual(0);
                expect(view.$('.join-team-message').length).toEqual(0);
            });

            it('shows already member message', function() {
                var requests = AjaxHelpers.requests(this);
                var currentUsername = 'ma1';
                var view =
                    createHeaderActionsView(
                        requests, 1, currentUsername, createTeamModelData('teamA', 'teamAlpha', []));

                // a get request will be sent to get user membership info
                // because current user is not member of current team
                AjaxHelpers.expectRequest(
                    requests,
                    'GET',
                    TeamSpecHelpers.testContext.teamMembershipsUrl + '?' + $.param({
                        username: currentUsername,
                        course_id: TeamSpecHelpers.testCourseID,
                        teamset_id: 'topic-id'
                    })
                );

                // current user is a member of another team so we should see the correct message
                AjaxHelpers.respondWithJson(requests, {count: 1});
                expect(view.$('.action.action-primary').length).toEqual(0);
                expect(view.$('.join-team-message').text().trim()).toBe(view.alreadyTeamsetMemberMessage);
            });

            it('shows team full message', function() {
                var requests = AjaxHelpers.requests(this);
                var view = createHeaderActionsView(
                    requests,
                    1,
                    'ma1',
                    createTeamModelData('teamA', 'teamAlpha', createMembershipData('ma'))
                );

                // team has no space and current user is a not member of
                // current team so we should see the correct message
                expect(view.$('.action.action-primary').length).toEqual(0);
                expect(view.$('.join-team-message').text().trim()).toBe(view.teamFullMessage);

                // there should be no request made
                AjaxHelpers.expectNoRequests(requests);
            });

            it('correctly resolves teamset-level max_size and course-level max_size', function() {
                var requests = AjaxHelpers.requests(this);
                var currentUsername = 'ma1';
                // Teamset maxSize = 2, Course maxSize = 1
                var view = createHeaderActionsView(
                    requests,
                    1,
                    'ma1',
                    createTeamModelData('teamA', 'teamAlpha', createMembershipData('ma')),
                    false,
                    false,
                    2
                );

                // Team should not be considered full with one member
                AjaxHelpers.expectRequest(
                    requests,
                    'GET',
                    TeamSpecHelpers.testContext.teamMembershipsUrl + '?' + $.param({
                        username: currentUsername,
                        course_id: TeamSpecHelpers.testCourseID,
                        teamset_id: 'topic-id'
                    })
                );

                // User is not a member of any teams
                AjaxHelpers.respondWithJson(requests, {count: 0});

                // Course-level size is 1, but Teamset size is 2, so that should take precedence
                // and we should see the Join Team Button
                expect(view.$('.action.action-primary').length).toEqual(1);
            });

            it('behaves correctly if the teamset max size is set to 0', function() {
                var requests = AjaxHelpers.requests(this);
                var currentUsername = 'ma1';
                // Teamset = 0, Course = 2
                var view = createHeaderActionsView(
                    requests,
                    2,
                    'ma1',
                    createTeamModelData('teamA', 'teamAlpha', createMembershipData('ma')),
                    false,
                    false,
                    0
                );

                // Team should not be considered full
                AjaxHelpers.expectRequest(
                    requests,
                    'GET',
                    TeamSpecHelpers.testContext.teamMembershipsUrl + '?' + $.param({
                        username: currentUsername,
                        course_id: TeamSpecHelpers.testCourseID,
                        teamset_id: 'topic-id'
                    })
                );

                // User is not a member of any teams
                AjaxHelpers.respondWithJson(requests, {count: 0});

                // Course-level size is 1 and Teamset size is 0, so course-level value should be used
                // and we should see the Join Team Button
                expect(view.$('.action.action-primary').length).toEqual(1);
            });

            it('shows not join instructor managed team message', function() {
                var requests = AjaxHelpers.requests(this);
                var currentUsername = 'ma1';
                var view = createHeaderActionsView(
                    requests,
                    1,
                    currentUsername,
                    createTeamModelData('teamA', 'teamAlpha', []),
                    false,
                    true);

                // a get request will be sent to get user membership info
                // because current user is not member of current team
                AjaxHelpers.expectRequest(
                    requests,
                    'GET',
                    TeamSpecHelpers.testContext.teamMembershipsUrl + '?' + $.param({
                        username: currentUsername,
                        course_id: TeamSpecHelpers.testCourseID,
                        teamset_id: 'topic-id'
                    })
                );

                // Mock the response so that current user is not a member of any team
                AjaxHelpers.respondWithJson(requests, {count: 0});

                // current user is a student and current team belogs to an instructor managed topic
                // so the Join Team button is hidden and we should see the correct message
                expect(view.$('.action.action-primary').length).toEqual(0);
                expect(view.$('.join-team-message').text().trim()).toBe(view.notJoinInstructorManagedTeam);
            });

            it('shows correct error message if user fails to join team', function() {
                var requests = AjaxHelpers.requests(this);

                // verify user_message
                verifyErrorMessage(
                    requests,
                    JSON.stringify({user_message: "Can't be made member"}),
                    "Can't be made member",
                    true
                );

                // verify generic error message
                verifyErrorMessage(
                    requests,
                    '',
                    'An error occurred. Try again.',
                    true
                );

                // verify error message when json parsing succeeded but error message format is incorrect
                verifyErrorMessage(
                    requests,
                    JSON.stringify({blah: "Can't be made member"}),
                    'An error occurred. Try again.',
                    true
                );
            });

            it('shows correct error message if initializing the view fails', function() {
                var requests = AjaxHelpers.requests(this);

                // verify user_message
                verifyErrorMessage(
                    requests,
                    JSON.stringify({user_message: "Can't return user memberships"}),
                    "Can't return user memberships",
                    false
                );

                // verify generic error message
                verifyErrorMessage(
                    requests,
                    '',
                    'An error occurred. Try again.',
                    false
                );
            });
        });

        describe('EditButton', function() {
            var teamModelData,
                view,
                createAndAssertView;

            createAndAssertView = function(requests, showEditButton) {
                teamModelData = createTeamModelData('aveA', 'avengers', createMembershipData('ma'));
                view = createHeaderActionsView(requests, 1, 'ma', teamModelData, showEditButton);
                expect(view.$('.action-edit-team').length).toEqual(showEditButton ? 1 : 0);
            };

            it('renders when option showEditButton is true', function() {
                var requests = AjaxHelpers.requests(this);
                createAndAssertView(requests, true);
            });

            it('does not render when option showEditButton is false', function() {
                var requests = AjaxHelpers.requests(this);
                createAndAssertView(requests, false);
            });

            it('can navigate to correct url', function() {
                var requests = AjaxHelpers.requests(this),
                    editButton;
                spyOn(Backbone.history, 'navigate');
                createAndAssertView(requests, true);
                editButton = view.$('.action-edit-team');

                expect(editButton.length).toEqual(1);
                $(editButton).click();

                expect(Backbone.history.navigate.calls.mostRecent().args[0]).toContain('/edit-team');
            });
        });
    });
});
