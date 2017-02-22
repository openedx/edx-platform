define([
    'jquery',
    'backbone',
    'underscore',
    'teams/js/models/team',
    'teams/js/views/instructor_tools',
    'teams/js/views/team_utils',
    'teams/js/spec_helpers/team_spec_helpers',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
    'common/js/spec_helpers/page_helpers'
], function($, Backbone, _, Team, InstructorToolsView, TeamUtils, TeamSpecHelpers, AjaxHelpers, PageHelpers) {
    'use strict';

    describe('Instructor Tools', function() {
        var view,
            createInstructorTools = function() {
                return new InstructorToolsView({
                    team: new Team(TeamSpecHelpers.createMockTeamData(1, 1)[0]),
                    teamEvents: TeamSpecHelpers.teamEvents
                });
            },
            deleteTeam = function(view, confirm) {
                view.$('.action-delete').click();
                // Confirm delete dialog
                if (confirm) {
                    $('.action-primary').click();
                }
                else {
                    $('.action-secondary').click();
                }
            },
            expectSuccessMessage = function(team) {
                expect(TeamUtils.showMessage).toHaveBeenCalledWith(
                    'Team "' + team.get('name') + '" successfully deleted.',
                    'success'
                );
            };

        beforeEach(function() {
            setFixtures('<div id="page-prompt"></div>');
            PageHelpers.preventBackboneChangingUrl();
            spyOn(Backbone.history, 'navigate');
            spyOn(TeamUtils, 'showMessage');
            view = createInstructorTools().render();
            spyOn(view.teamEvents, 'trigger');
        });

        it('can render itself', function() {
            expect(_.strip(view.$('.action-delete').text())).toEqual('Delete Team');
            expect(_.strip(view.$('.action-edit-members').text())).toEqual('Edit Membership');
            expect(view.$el.text()).toContain('Instructor tools');
        });

        it('can delete a team and shows a success message', function() {
            var requests = AjaxHelpers.requests(this);
            deleteTeam(view, true);
            AjaxHelpers.expectJsonRequest(requests, 'DELETE', view.team.url, null);
            AjaxHelpers.respondWithNoContent(requests);
            expect(Backbone.history.navigate).toHaveBeenCalledWith(
                'topics/' + view.team.get('topic_id'),
                {trigger: true}
            );
            expect(view.teamEvents.trigger).toHaveBeenCalledWith(
                'teams:update', {
                    action: 'delete',
                    team: view.team
                }
            );
            expectSuccessMessage(view.team);
        });

        it('can cancel team deletion', function() {
            var requests = AjaxHelpers.requests(this);
            deleteTeam(view, false);
            AjaxHelpers.expectNoRequests(requests);
            expect(Backbone.history.navigate).not.toHaveBeenCalled();
        });

        it('shows a success message after receiving a 404', function() {
            var requests = AjaxHelpers.requests(this);
            deleteTeam(view, true);
            AjaxHelpers.respondWithError(requests, 404);
            expectSuccessMessage(view.team);
        });

        it('can trigger the edit membership view', function() {
            view.$('.action-edit-members').click();
            expect(Backbone.history.navigate).toHaveBeenCalledWith(
                'teams/' + view.team.get('topic_id') + '/' + view.team.id + '/edit-team/manage-members',
                {trigger: true}
            );
        });
    });
});
