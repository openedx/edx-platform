define([
    'jquery',
    'backbone',
    'teams/js/models/team',
    'teams/js/views/instructor_tools',
    'teams/js/spec_helpers/team_spec_helpers',
    'common/js/spec_helpers/ajax_helpers'
], function ($, Backbone, Team, InstructorToolsView, TeamSpecHelpers, AjaxHelpers) {
    'use strict';

    describe('Instructor Tools', function () {
        var view,
            createInstructorTools = function () {
                return new InstructorToolsView({
                    team: new Team(TeamSpecHelpers.createMockTeamData(1, 1)[0]),
                    teamEvents: TeamSpecHelpers.teamEvents
                });
            },
            deleteTeam = function (view, confirm) {
                view.$('.action-delete').click();
                // Confirm delete dialog
                if (confirm) {
                    $('.action-primary').click();
                }
                else {
                    $('.action-secondary').click();
                }
            };

        beforeEach(function () {
            setFixtures('<div id="page-prompt"></div>');
            spyOn(Backbone.history, 'navigate');
            view = createInstructorTools().render();
            spyOn(view.teamEvents, 'trigger');
        });

        it('can render itself', function () {
            expect(_.strip(view.$('.action-delete').text())).toEqual('Delete Team');
            expect(_.strip(view.$('.action-edit-members').text())).toEqual('Edit Membership');
            expect(view.$el.text()).toContain('Instructor tools');
        });

        it('can trigger the edit membership view', function () {
            view.$('.action-edit-members').click();
            expect(Backbone.history.navigate).toHaveBeenCalledWith(
                'topics/' + view.team.get('topic_id') + "/" + view.team.id + "/edit-team/manage-members",
                {trigger: true}
            );
        });
    });
});
