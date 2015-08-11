define([
    'jquery',
    'backbone',
    'teams/js/views/team_actions'
], function ($, Backbone, TeamActionsView) {
    'use strict';

    describe('TeamActions', function () {
        var teamActionsView;

        beforeEach(function () {
            setFixtures('<div class="teams-content"></div>');
            spyOn(Backbone.history, 'navigate');
            teamActionsView = new TeamActionsView({
                el: $('.teams-content'),
                teamParams: {topicId: 'awesomeness'}
            }).render();
        });

        it('can render itself correctly', function () {
            expect(teamActionsView.$('.title').text()).toBe('Are you having trouble finding a team to join?');
            expect(teamActionsView.$('.copy').text()).toBe(
                "Try browsing all teams or searching team descriptions. If you " +
                "still can't find a team to join, create a new team in this topic."
            );
        });

        it('can navigate to correct routes', function () {
            teamActionsView.$('a.browse-teams').click();
            expect(Backbone.history.navigate.calls[0].args).toContain('browse');

            teamActionsView.$('a.search-team-descriptions').click();
            // TODO! Should be updated once team description search feature is available
            expect(Backbone.history.navigate.calls[1].args).toContain('browse');

            teamActionsView.$('a.create-team').click();
            expect(Backbone.history.navigate.calls[2].args).toContain('topics/awesomeness/create-team');
        });
    });
});
