define([
    'jquery',
    'underscore',
    'backbone',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
    'teams/js/views/edit_team_members',
    'teams/js/models/team',
    'teams/js/views/team_utils',
    'teams/js/spec_helpers/team_spec_helpers'
], function($, _, Backbone, AjaxHelpers, TeamEditMembershipView, TeamModel, TeamUtils, TeamSpecHelpers) {
    'use strict';

    describe('CreateEditTeam', function() {
        var editTeamID = 'av',
            DEFAULT_MEMBERSHIP = [
                {
                    user: {
                        username: 'frodo',
                        profile_image: {
                            has_image: true,
                            image_url_medium: '/frodo-image-url'
                        }
                    },
                    last_activity_at: '2015-08-21T18:53:01.145Z',
                    date_joined: '2014-01-01T18:53:01.145Z'
                }
            ],
            deleteTeamMemember = function(view, confirm) {
                view.$('.action-remove-member').click();
                // Confirm delete dialog
                if (confirm) {
                    $('.action-primary').click();
                } else {
                    $('.action-secondary').click();
                }
            },
            verifyTeamMembersView = function(view) {
                expect(view.$('.team-member').length).toEqual(1);
                expect(view.$('.member-profile').attr('href')).toEqual('/u/frodo');
                expect(view.$('img.image-url').attr('src')).toEqual('/frodo-image-url');
                expect(view.$('.member-info-container .primary').text()).toBe('frodo');
                expect(view.$el.find('#last-active abbr').attr('title')).toEqual('2015-08-21T18:53:01.145Z');
                expect(view.$el.find('#date-joined abbr').attr('title')).toEqual('2014-01-01T18:53:01.145Z');
            },
            verifyNoMembersView = function(view) {
                expect(view.$el.text().trim()).toBe('This team does not have any members.');
            },
            createTeamModelData = function(membership) {
                return {
                    id: editTeamID,
                    name: 'Avengers',
                    description: 'Team of dumbs',
                    language: 'en',
                    country: 'US',
                    membership: membership,
                    url: '/api/team/v0/teams/' + editTeamID
                };
            },
            createEditTeamMembersView = function(membership) {
                var teamModel = new TeamModel(
                    createTeamModelData(membership),
                    {parse: true}
                );

                return new TeamEditMembershipView({
                    teamEvents: TeamSpecHelpers.teamEvents,
                    el: $('.teams-content'),
                    model: teamModel,
                    context: TeamSpecHelpers.testContext
                }).render();
            };

        beforeEach(function() {
            setFixtures('<div id="page-prompt"></div><div class="teams-content"></div>');
            spyOn(Backbone.history, 'navigate');
            spyOn(TeamUtils, 'showMessage');
        });

        it('can render a message when there are no members', function() {
            var view = createEditTeamMembersView([]);
            verifyNoMembersView(view);
        });

        it('can delete a team member and update the view', function() {
            var requests = AjaxHelpers.requests(this),
                view = createEditTeamMembersView(DEFAULT_MEMBERSHIP);

            spyOn(view.teamEvents, 'trigger');
            verifyTeamMembersView(view);

            deleteTeamMemember(view, true);
            AjaxHelpers.expectJsonRequest(
                requests,
                'DELETE',
                '/api/team/v0/team_membership/av,frodo?admin=true'
            );
            AjaxHelpers.respondWithNoContent(requests);
            expect(view.teamEvents.trigger).toHaveBeenCalledWith(
                'teams:update', {
                    action: 'leave',
                    team: view.model
                }
            );
            AjaxHelpers.expectJsonRequest(requests, 'GET', view.model.get('url'));
            AjaxHelpers.respondWithJson(requests, createTeamModelData([]));

            verifyNoMembersView(view);
        });

        it('can show an error message if removing the user fails', function() {
            var requests = AjaxHelpers.requests(this),
                view = createEditTeamMembersView(DEFAULT_MEMBERSHIP);

            spyOn(view.teamEvents, 'trigger');
            verifyTeamMembersView(view);

            deleteTeamMemember(view, true);
            AjaxHelpers.expectJsonRequest(
                requests,
                'DELETE',
                '/api/team/v0/team_membership/av,frodo?admin=true'
            );
            AjaxHelpers.respondWithError(requests);
            expect(TeamUtils.showMessage).toHaveBeenCalledWith(
                'An error occurred while removing the member from the team. Try again.',
                undefined
            );
            expect(view.teamEvents.trigger).not.toHaveBeenCalled();
            verifyTeamMembersView(view);
        });

        it('can cancel team membership deletion', function() {
            var requests = AjaxHelpers.requests(this);
            var view = createEditTeamMembersView(DEFAULT_MEMBERSHIP);

            spyOn(view.teamEvents, 'trigger');
            verifyTeamMembersView(view);

            deleteTeamMemember(view, false);
            AjaxHelpers.expectNoRequests(requests);
            expect(view.teamEvents.trigger).not.toHaveBeenCalled();
            verifyTeamMembersView(view);
        });
    });
});
