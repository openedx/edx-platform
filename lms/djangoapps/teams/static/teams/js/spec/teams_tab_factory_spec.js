define(['jquery', 'backbone', 'teams/js/teams_tab_factory', 'teams/js/views/teams_tab',
        'common/js/spec_helpers/page_helpers', 'teams/js/spec_helpers/team_spec_helpers'],
    function($, Backbone, TeamsTabFactory, TeamsTabView, PageHelpers, TeamSpecHelpers) {
        'use strict';

        describe("Teams Tab Factory", function() {
            var initializeTeamsTabFactory = function() {
                TeamsTabFactory(TeamSpecHelpers.createMockContext());
            };

            beforeEach(function() {
                setFixtures('<section class="teams-content"></section>');
                PageHelpers.preventBackboneChangingUrl();
            });

            afterEach(function() {
                Backbone.history.stop();
                $(document).off('ajaxError', TeamsTabView.prototype.errorHandler);
            });

            it('can render the "Teams" tab', function() {
                initializeTeamsTabFactory();
                expect($('.teams-content').text()).toContain('See all teams in your course, organized by topic');
            });
        });
    }
);
