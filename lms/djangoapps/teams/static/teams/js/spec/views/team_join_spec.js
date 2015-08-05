define([
    'underscore', 'common/js/spec_helpers/ajax_helpers', 'teams/js/models/team',
    'teams/js/views/team_join', 'teams/js/views/team_profile'
], function (_, AjaxHelpers, TeamModel, TeamJoinView, TeamProfileView) {
    'use strict';
    describe('TeamJoinView', function () {
        var createTeamModelData,
            createMembershipData,
            createJoinView,
            teamProfileView,
            ACCOUNTS_API_URL = '/api/user/v1/accounts/',
            TEAMS_URL = '/api/team/v0/teams/',
            TEAMS_MEMBERSHIP_URL = '/api/team/v0/team_membership/';

        beforeEach(function () {
            setFixtures(
                '<div class="msg-content"><div class="copy"></div></div><div class="header-action-view"></div>'
            );
        });

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

        createJoinView = function(maxTeamSize, currentUsername, teamModelData) {
            var model = new TeamModel(teamModelData, { parse: true });
            teamProfileView = new TeamProfileView(
                {
                    model: model,
                    teamsUrl: TEAMS_URL,
                    maxTeamSize: maxTeamSize,
                    currentUsername: currentUsername,
                }
            );

            var teamJoinView = new TeamJoinView(
                {
                    model: model,
                    teamsUrl: TEAMS_URL,
                    maxTeamSize: maxTeamSize,
                    currentUsername: currentUsername,
                    teamsMembershipUrl: TEAMS_MEMBERSHIP_URL
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
                TEAMS_MEMBERSHIP_URL + '?' + $.param({"username": currentUsername})
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
                TEAMS_URL + teamId
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
                TEAMS_MEMBERSHIP_URL + '?' + $.param({"username": currentUsername})
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

        it('shows correct error messages', function () {
            var requests = AjaxHelpers.requests(this);

            var verifyErrorMessage = function (requests, errorMessage, expectedMessage) {
                createJoinView(1, 'ma', createTeamModelData('teamA', 'teamAlpha', []));
                AjaxHelpers.respondWithTextError(requests, 400, errorMessage);
                expect($('.msg-content .copy').text().trim()).toBe(expectedMessage);
            };

            // verify user_message
            verifyErrorMessage(
                requests,
                JSON.stringify({'user_message': 'Awesome! You got an error.'}),
                'Awesome! You got an error.'
            );

            // verify generic error message
            verifyErrorMessage(
                requests,
                '',
                'An error occurred. Try again.'
            );
        });
    });
});
