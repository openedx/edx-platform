define([
    'underscore', 'common/js/spec_helpers/ajax_helpers', 'teams/js/models/team',
    'teams/js/views/team_profile', 'teams/js/spec_helpers/team_spec_helpers',
    'xmodule_js/common_static/coffee/spec/discussion/discussion_spec_helper'
], function (_, AjaxHelpers, TeamModel, TeamProfileView, TeamSpecHelpers, DiscussionSpecHelper) {
    'use strict';
    describe('TeamProfileView', function () {
        var profileView, createTeamProfileView;

        beforeEach(function () {
            DiscussionSpecHelper.setUnderscoreFixtures();
        });

        createTeamProfileView = function(requests, options) {
            var model = new TeamModel(
                {
                    id: "test-team",
                    name: "Test Team",
                    discussion_topic_id: TeamSpecHelpers.testTeamDiscussionID,
                    country: options.country || '',
                    language: options.language || '',
                    membership: options.membership || []
                },
                { parse: true }
            );
            profileView = new TeamProfileView({
                courseID: TeamSpecHelpers.testCourseID,
                model: model,
                maxTeamSize: options.maxTeamSize || 3,
                requestUsername: 'bilbo',
                countries : [
                    ['', ''],
                    ['US', 'United States'],
                    ['CA', 'Canada']
                ],
                languages : [
                    ['', ''],
                    ['en', 'English'],
                    ['fr', 'French']
                ]
            });
            profileView.render();
            AjaxHelpers.expectRequest(
                requests,
                'GET',
                interpolate(
                    '/courses/%(courseID)s/discussion/forum/%(topicID)s/inline?page=1&ajax=1',
                    {
                        courseID: TeamSpecHelpers.testCourseID,
                        topicID: TeamSpecHelpers.testTeamDiscussionID
                    },
                    true
                )
            );
            AjaxHelpers.respondWithJson(requests, TeamSpecHelpers.createMockDiscussionResponse());
            return profileView;
        };

        describe('DiscussionsView', function() {
            it('can render itself', function () {
                var requests = AjaxHelpers.requests(this),
                    view = createTeamProfileView(requests, {});
                expect(view.$('.discussion-thread').length).toEqual(3);
            });
        });

        describe('TeamDetailsView', function() {

            var assertTeamDetails = function(view, members) {
                expect(view.$('.team-detail-header').text()).toBe('Team Details');
                expect(view.$('.team-country').text()).toContain('United States');
                expect(view.$('.team-language').text()).toContain('English');
                expect(view.$('.team-capacity').text()).toContain(members + ' / 3 Members');
                expect(view.$('.team-member').length).toBe(members);
            };

            describe('Non-Member', function() {

                it('can render itself', function() {
                    var requests = AjaxHelpers.requests(this);
                    var view = createTeamProfileView(requests, {
                        country: 'US',
                        language: 'en'
                    });
                    assertTeamDetails(view, 0);
                    expect(view.$('.team-user-membership-status').length).toBe(0);

                    // Verify that invite and leave team sections are not present.
                    expect(view.$('.leave-team').length).toBe(0);
                    expect(view.$('.invite-team').length).toBe(0);

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
                        membership: [{
                            'user': {
                                'username': 'bilbo',
                                'profile_image': {
                                    'has_image': true,
                                    'image_url_medium': '/image-url'
                                }
                            }
                        }]
                    });
                    assertTeamDetails(view, 1);
                    expect(view.$('.team-user-membership-status').text().trim()).toBe('You are a member of this team.');

                    // assert tooltip text.
                    expect(view.$('.member-profile p').text()).toBe('bilbo');
                    // assert user profile page url.
                    expect(view.$('.member-profile').attr('href')).toBe('/u/bilbo');

                    //Verify that invite and leave team sections are present
                    expect(view.$('.leave-team-link').text()).toContain('Leave Team');
                    expect(view.$('.invite-header').text()).toContain('Invite Others');
                    expect(view.$('.invite-text').text()).toContain('Send this link to friends so that they can join too.');
                    expect(view.$('.invite-link-input').length).toBe(1);

                });
                it('cannot see invite url box if team is full', function() {
                    var requests = AjaxHelpers.requests(this);
                    var view = createTeamProfileView(requests , {
                        country: 'US',
                        language: 'en',
                        membership: [{
                            'user': {
                                'username': 'bilbo',
                                'profile_image': {
                                    'has_image': true,
                                    'image_url_medium': '/image-url'
                                }
                            }
                        },
                        {
                            'user': {
                                'username': 'bilbo1',
                                'profile_image': {
                                    'has_image': true,
                                    'image_url_medium': '/image-url'
                                }
                            }
                        },
                        {
                            'user': {
                                'username': 'bilbo2',
                                'profile_image': {
                                    'has_image': true,
                                    'image_url_medium': '/image-url'
                                }
                            }
                        }]
                    });

                    assertTeamDetails(view, 3);
                    expect(view.$('.invite-header').text()).toContain('Invite Others');
                    expect(view.$('.invite-text').text()).toContain('No invitations are available. This team is full.');
                    expect(view.$('.invite-link-input').length).toBe(0);
                });
                it('can see & select invite url if team has capacity', function() {
                    var requests = AjaxHelpers.requests(this);
                    spyOn(TeamProfileView.prototype, 'selectText');

                    var view = createTeamProfileView(requests, {
                        country: 'US',
                        language: 'en',
                        membership: [{
                            'user': {
                                'username': 'bilbo',
                                'profile_image': {
                                    'has_image': true,
                                    'image_url_medium': '/image-url'
                                }
                            }
                        }]
                    });
                    assertTeamDetails(view, 1);

                    expect(view.$('.invite-link-input').length).toBe(1);

                    view.$('.invite-link-input').click();
                    expect(view.selectText).toHaveBeenCalled();
                });
            });
        });
    });
});
