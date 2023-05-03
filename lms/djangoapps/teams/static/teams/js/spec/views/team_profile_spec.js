define([
    'underscore',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
    'common/js/spec_helpers/discussion_spec_helper',
    'teams/js/spec_helpers/team_spec_helpers',
    'teams/js/models/team',
    'teams/js/views/team_profile'
], function(_, AjaxHelpers, DiscussionSpecHelper, TeamSpecHelpers, TeamModel, TeamProfileView) {
    'use strict';
    describe('TeamProfileView', function() {
        var profileView, createTeamProfileView, createTeamModelData, clickLeaveTeam,
            teamModel,
            leaveTeamLinkSelector = '.leave-team-link',
            DEFAULT_MEMBERSHIP = [
                {
                    user: {
                        username: TeamSpecHelpers.testUser,
                        profile_image: {
                            has_image: true,
                            image_url_medium: '/image-url'
                        }
                    }
                }
            ];

        beforeEach(function() {
            setFixtures('<div id="page-prompt"></div>' +
                '<div class="teams-content"><div class="msg-content"><div class="copy"></div></div></div>' +
                '<div class="profile-view"></div>');
            DiscussionSpecHelper.setUnderscoreFixtures();
        });

        createTeamModelData = function(options) {
            return {
                id: 'test-team',
                name: 'Test Team',
                discussion_topic_id: TeamSpecHelpers.testTeamDiscussionID,
                country: options.country || '',
                language: options.language || '',
                membership: options.membership || [],
                url: '/api/team/v0/teams/test-team'
            };
        };

        createTeamProfileView = function(requests, options, isInstructorManagedTopic) {
            teamModel = new TeamModel(createTeamModelData(options), {parse: true});
            profileView = new TeamProfileView({
                el: $('.profile-view'),
                teamEvents: TeamSpecHelpers.teamEvents,
                courseID: TeamSpecHelpers.testCourseID,
                context: options.context || TeamSpecHelpers.testContext,
                model: teamModel,
                topic: isInstructorManagedTopic ?
                    TeamSpecHelpers.createMockTopic({type: 'public_managed'}) :
                    TeamSpecHelpers.createMockTopic(),
                setFocusToHeaderFunc: function() {
                    $('.teams-content').focus();
                }
            });
            profileView.render();
            AjaxHelpers.expectRequest(
                requests,
                'GET',
                interpolate( // eslint-disable-line no-undef
                    '/courses/%(courseID)s/discussion/forum/%(topicID)s/inline' +
                    '?page=1&sort_key=activity&sort_order=desc&ajax=1',
                    {
                        courseID: TeamSpecHelpers.testCourseID,
                        topicID: TeamSpecHelpers.testTeamDiscussionID
                    },
                    true
                )
            );
            AjaxHelpers.respondWithJson(requests, TeamSpecHelpers.createMockDiscussionResponse());

            // Assignments are feature-flagged
            if (profileView.context.teamsAssignmentsUrl) {
                AjaxHelpers.expectRequest(
                    requests,
                    'GET',
                    interpolate( // eslint-disable-line no-undef
                        '/api/team/v0/teams/%(teamId)s/assignments',
                        {
                            teamId: teamModel.id
                        },
                        true
                    )
                );
                AjaxHelpers.respondWithJson(requests, TeamSpecHelpers.createMockTeamAssignments(options.assignments));
            }

            return profileView;
        };

        clickLeaveTeam = function(requests, view, options) {
            expect(view.$(leaveTeamLinkSelector).length).toBe(1);

            // click on Leave Team link under Team Details
            view.$(leaveTeamLinkSelector).click();

            if (!options.cancel) {
                // click on Confirm button on dialog
                $('.prompt.warning .action-primary').click();

                // expect a request to DELETE the team membership
                AjaxHelpers.expectJsonRequest(
                    requests, 'DELETE', '/api/team/v0/team_membership/test-team,' + TeamSpecHelpers.testUser
                );
                AjaxHelpers.respondWithNoContent(requests);

                // expect a request to refetch the user's team memberships
                AjaxHelpers.expectJsonRequest(requests, 'GET', '/api/team/v0/teams/test-team');
                AjaxHelpers.respondWithJson(requests, createTeamModelData({country: 'US', language: 'en'}));
            } else {
                // click on Cancel button on dialog
                $('.prompt.warning .action-secondary').click();
                AjaxHelpers.expectNoRequests(requests);
            }
        };

        describe('TeamAssignmentsView', function() {
            it('can render itself', function() {
                // Given a member of a team with team assignments
                var mockAssignments = TeamSpecHelpers.createMockTeamAssignments(),
                    options = {
                        membership: DEFAULT_MEMBERSHIP
                    },
                    requests = AjaxHelpers.requests(this);

                // When they go to the team profile view
                var view = createTeamProfileView(requests, options);

                // The Assignments section renders with their assignments
                expect(view.$('.team-assignment').length).toEqual(mockAssignments.length);
            });

            it('displays a message when no assignments are found', function() {
                // Given a member viewing a team with no assignments
                var mockAssignments = [],
                    options = {
                        assignments: mockAssignments,
                        membership: DEFAULT_MEMBERSHIP
                    },
                    requests = AjaxHelpers.requests(this);

                // When they view the team
                var view = createTeamProfileView(requests, options);

                // There should be filler text that says there are no assignments
                expect(view.$('#assignments').text()).toEqual('No assignments for team');
                expect(view.$('.team-assignment').length).toEqual(0);
            });

            it('does not show at all for someone who is not on the team or staff', function() {
                // Given a user who is not on a team viewing a team with assignments
                var mockAssignments = TeamSpecHelpers.createMockTeamAssignments(),
                    options = {
                        assignments: mockAssignments
                    },
                    requests = AjaxHelpers.requests(this);

                // When the user goes to the team detail page
                var view = createTeamProfileView(requests, options);

                // Then then assignments view does not appear on the page
                expect(view.$('.team-assignments').length).toBe(0);
            });

            it('does not show at all when the feature flag is turned off', function() {
                // Given the team submissions feature is turned off
                // (teamAsssignmentsUrl isn't surfaced to user)
                var mockAssignments = TeamSpecHelpers.createMockTeamAssignments(),
                    options = {
                        assignments: mockAssignments,
                        membership: DEFAULT_MEMBERSHIP,
                        context: Object.assign({}, TeamSpecHelpers.testContext)
                    },
                    requests = AjaxHelpers.requests(this),
                    view;

                delete options.context.teamsAssignmentsUrl;

                // When the user goes to the team detail page
                view = createTeamProfileView(requests, options);

                // Then then assignments view does not appear on the page
                expect(view.$('.team-assignments').length).toBe(0);
            });
        });

        describe('DiscussionsView', function() {
            it('can render itself', function() {
                var requests = AjaxHelpers.requests(this),
                    view = createTeamProfileView(requests, {});
                expect(view.$('.forum-nav-thread').length).toEqual(3);
            });

            it('shows New Post button when user joins a team', function() {
                var requests = AjaxHelpers.requests(this),
                    view = createTeamProfileView(requests, {});

                teamModel.set('membership', DEFAULT_MEMBERSHIP);  // This should re-render the view.
                view.render();
                expect(view.$('.btn-link.new-post-btn.is-hidden').length).toEqual(0);
            });

            it('hides New Post button when user left a team', function() {
                var requests = AjaxHelpers.requests(this),
                    view = createTeamProfileView(requests, {membership: DEFAULT_MEMBERSHIP});

                clickLeaveTeam(requests, view, {cancel: false});
                expect(view.$('.new-post-btn.is-hidden').length).toEqual(0);
            });

            it('shows New Post button when user is a staff member or admin', function() {
                var requests = AjaxHelpers.requests(this),
                    view = createTeamProfileView(
                        requests, {userInfo: TeamSpecHelpers.createMockUserInfo({staff: true})}
                    );

                view.render();
                expect(view.$('.btn-link.new-post-btn.is-hidden').length).toEqual(0);
            });
        });

        describe('TeamDetailsView', function() {
            var assertTeamDetails = function(view, members, memberOfTeam, isManagedTeam) {
                var expectedMemberMsg;
                expect(view.$('.team-detail-header').text()).toBe('Team Details');
                expect(view.$('.team-country').text()).toContain('United States');
                expect(view.$('.team-language').text()).toContain('English');
                if (isManagedTeam) {
                    if (members === 1) {
                        expectedMemberMsg = '1 Member';
                    } else {
                        expectedMemberMsg = members + ' Members';
                    }
                } else {
                    expectedMemberMsg = members + ' / 6 Members';
                }
                expect(view.$('.team-capacity').text()).toContain(expectedMemberMsg);
                expect(view.$('.team-member').length).toBe(members);
                expect(Boolean(view.$('.leave-team-link').length)).toBe(memberOfTeam);
            };

            describe('Non-Member', function() {
                it('can render itself', function() {
                    var requests = AjaxHelpers.requests(this);
                    var view = createTeamProfileView(requests, {
                        country: 'US',
                        language: 'en'
                    });
                    assertTeamDetails(view, 0, false, false);
                    expect(view.$('.team-user-membership-status').length).toBe(0);

                    // Verify that the leave team link is not present.
                    expect(view.$(leaveTeamLinkSelector).length).toBe(0);
                });

                it('cannot see the country & language if empty', function() {
                    var requests = AjaxHelpers.requests(this);
                    var view = createTeamProfileView(requests, {});
                    expect(view.$('.team-country').length).toBe(0);
                    expect(view.$('.team-language').length).toBe(0);
                });
            });

            describe('Member', function() {
                it('can render itself', function() {
                    var requests = AjaxHelpers.requests(this);
                    var view = createTeamProfileView(requests, {
                        country: 'US',
                        language: 'en',
                        membership: DEFAULT_MEMBERSHIP
                    });
                    assertTeamDetails(view, 1, true, false);
                    expect(view.$('.team-user-membership-status').text().trim()).toBe('You are a member of this team.');

                    // assert tooltip text.
                    expect(view.$('.member-profile p').text()).toBe(TeamSpecHelpers.testUser);
                    // assert user profile page url.
                    expect(view.$('.member-profile').attr('href')).toBe('/u/' + TeamSpecHelpers.testUser);

                    // Verify that the leave team link is present
                    expect(view.$(leaveTeamLinkSelector).text()).toContain('Leave Team');
                });

                it('can leave team successfully', function() {
                    var requests = AjaxHelpers.requests(this);

                    var view = createTeamProfileView(
                        requests, {country: 'US', language: 'en', membership: DEFAULT_MEMBERSHIP}
                    );
                    assertTeamDetails(view, 1, true, false);
                    clickLeaveTeam(requests, view, {cancel: false});
                    assertTeamDetails(view, 0, false, false);
                });

                it('student can not leave instructor managed team', function() {
                    var requests = AjaxHelpers.requests(this);

                    var view = createTeamProfileView(
                        requests, {country: 'US', language: 'en', membership: DEFAULT_MEMBERSHIP}, true
                    );
                    // When a student is in a team of an instructor-managed topic, he can't see the leave team button.
                    assertTeamDetails(view, 1, false, true);
                });

                it("wouldn't do anything if user click on Cancel button on dialog", function() {
                    var requests = AjaxHelpers.requests(this);

                    var view = createTeamProfileView(
                        requests, {country: 'US', language: 'en', membership: DEFAULT_MEMBERSHIP}
                    );
                    assertTeamDetails(view, 1, true, false);
                    clickLeaveTeam(requests, view, {cancel: true});
                    assertTeamDetails(view, 1, true, false);
                });

                it('shows correct error messages', function() {
                    var requests = AjaxHelpers.requests(this);

                    var verifyErrorMessage = function(errorMessage, expectedMessage) {
                        var view = createTeamProfileView(
                            requests, {country: 'US', language: 'en', membership: DEFAULT_MEMBERSHIP}
                        );
                        // click leave team link
                        view.$('.leave-team-link').click();
                        // click Confirm button on dialog
                        $('.prompt.warning .action-primary').click();
                        AjaxHelpers.respondWithTextError(requests, 400, errorMessage);
                        expect($('.msg-content .copy').text().trim()).toBe(expectedMessage);
                    };

                    // verify user_message
                    verifyErrorMessage(
                        JSON.stringify({user_message: "can't remove user from team"}),
                        "can't remove user from team"
                    );

                    // verify generic error message
                    verifyErrorMessage(
                        '',
                        'An error occurred. Try again.'
                    );

                    // verify error message when json parsing succeeded but error message format is incorrect
                    verifyErrorMessage(
                        JSON.stringify({blah: "can't remove user from team"}),
                        'An error occurred. Try again.'
                    );
                });
            });
        });
    });
});
