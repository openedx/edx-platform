define([
    'backbone', 'underscore', 'common/js/spec_helpers/ajax_helpers', 'teams/js/models/team',
    'teams/js/views/team_join', 'teams/js/spec_helpers/team_spec_helpers'
], function (Backbone, _, AjaxHelpers, TeamModel, TeamJoinView, TeamSpecHelpers) {
    'use strict';
    describe('TeamJoinView', function () {
        var createTeamsUrl,
            createTeamModelData,
            createMembershipData,
            createJoinView,
            verifyErrorMessage,
            ACCOUNTS_API_URL = '/api/user/v1/accounts/',
            TEAMS_URL = '/api/team/v0/teams/',
            TEAMS_MEMBERSHIP_URL = '/api/team/v0/team_membership/';

        beforeEach(function () {
            setFixtures(
                '<div class="teams-content"><div class="msg-content"><div class="copy"></div></div><div class="header-action-view"></div></div>'
            );
        });

        verifyErrorMessage = function (requests, errorMessage, expectedMessage, joinTeam) {
            var view = createJoinView(1, 'ma', createTeamModelData('teamA', 'teamAlpha', []));
            if (joinTeam) {
                // if we want the error to return when user try to join team, respond with no membership
                AjaxHelpers.respondWithJson(requests, {"count": 0});
                view.$('.action.action-primary').click();
            }
            AjaxHelpers.respondWithTextError(requests, 400, errorMessage);
            expect($('.msg-content .copy').text().trim()).toBe(expectedMessage);
        };

        createTeamsUrl = function (teamId) {
            return TEAMS_URL + teamId + '?expand=user';
        };

        createTeamModelData = function (teamId, teamName, membership) {
            return  {
                id: teamId,
                name: teamName,
                membership: membership
            };
        };

        createMembershipData = function (username) {
            return [
                {
                    "user": {
                    "username": username,
                    "url": ACCOUNTS_API_URL + username
                    }
                }
            ];
        };

        createJoinView = function(maxTeamSize, currentUsername, teamModelData, teamId) {
            teamId = teamId || 'teamA';

            var model = new TeamModel(teamModelData, { parse: true });
            model.url = createTeamsUrl(teamId);

            var teamJoinView = new TeamJoinView(
                {
                    courseID: TeamSpecHelpers.testCourseID,
                    teamEvents: TeamSpecHelpers.teamEvents,
                    model: model,
                    teamsUrl: createTeamsUrl(teamId),
                    maxTeamSize: maxTeamSize,
                    currentUsername: currentUsername,
                    teamMembershipsUrl: TEAMS_MEMBERSHIP_URL
                }
            );
            return teamJoinView.render();
        };

        it('can render itself', function () {
            var teamModelData = createTeamModelData('teamA', 'teamAlpha', createMembershipData('ma'));
            var view = createJoinView(1, 'ma', teamModelData);

            expect(view.$('.join-team').length).toEqual(1);
        });

        it('can join team successfully', function () {
            var requests = AjaxHelpers.requests(this);
            var currentUsername = 'ma1';
            var teamId = 'teamA';
            var teamName = 'teamAlpha';
            var teamModelData = createTeamModelData(teamId, teamName, []);
            var view = createJoinView(1, currentUsername, teamModelData);

            // a get request will be sent to get user membership info
            // because current user is not member of current team
            AjaxHelpers.expectRequest(
                requests,
                'GET',
                TEAMS_MEMBERSHIP_URL + '?' + $.param({
                    'username': currentUsername, 'course_id': TeamSpecHelpers.testCourseID
                })
            );

            // current user is not a member of any team so we should see the Join Team button
            AjaxHelpers.respondWithJson(requests, {"count": 0});
            expect(view.$('.action.action-primary').length).toEqual(1);

            // a post request will be sent to add current user to current team
            view.$('.action.action-primary').click();
            AjaxHelpers.expectRequest(
                requests,
                'POST',
                TEAMS_MEMBERSHIP_URL,
                $.param({'username': currentUsername, 'team_id': teamId})
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

        it('shows already member message', function () {
            var requests = AjaxHelpers.requests(this);
            var currentUsername = 'ma1';
            var view = createJoinView(1, currentUsername, createTeamModelData('teamA', 'teamAlpha', []));

            // a get request will be sent to get user membership info
            // because current user is not member of current team
            AjaxHelpers.expectRequest(
                requests,
                'GET',
                TEAMS_MEMBERSHIP_URL + '?' + $.param({
                    'username': currentUsername, 'course_id': TeamSpecHelpers.testCourseID
                })
            );

            // current user is a member of another team so we should see the correct message
            AjaxHelpers.respondWithJson(requests, {"count": 1});
            expect(view.$('.action.action-primary').length).toEqual(0);
            expect(view.$('.join-team-message').text().trim()).toBe(view.alreadyMemberMessage);
        });

        it('shows team full message', function () {
            var requests = AjaxHelpers.requests(this);
            var view = createJoinView(
                1,
                'ma1',
                createTeamModelData('teamA', 'teamAlpha', createMembershipData('ma'))
            );

            // team has no space and current user is a not member of
            // current team so we should see the correct message
            expect(view.$('.action.action-primary').length).toEqual(0);
            expect(view.$('.join-team-message').text().trim()).toBe(view.teamFullMessage);

            // there should be no request made
            expect(requests.length).toBe(0);
        });

        it('shows correct error message if user fails to join team', function () {
            var requests = AjaxHelpers.requests(this);

            // verify user_message
            verifyErrorMessage(
                requests,
                JSON.stringify({'user_message': "Can't be made member"}),
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
                JSON.stringify({'blah': "Can't be made member"}),
                'An error occurred. Try again.',
                true
            );
        });

        it('shows correct error message if initializing the view fails', function () {
            // Rendering the view sometimes require fetching user's memberships. This may fail.
            var requests = AjaxHelpers.requests(this);

            // verify user_message
            verifyErrorMessage(
                requests,
                JSON.stringify({'user_message': "Can't return user memberships"}),
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
});
