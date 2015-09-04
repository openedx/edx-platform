define(['jquery', 'backbone', 'teams/js/teams_tab_factory',
        'teams/js/spec_helpers/team_spec_helpers'],
    function($, Backbone, TeamsTabFactory, TeamSpecHelpers) {
        'use strict';

        describe("Teams Tab Factory", function() {
            var initializeTeamsTabFactory = function() {
                TeamsTabFactory(TeamSpecHelpers.createMockContext());
            };

            beforeEach(function() {
                setFixtures('<section class="teams-content"></section>');
            });

            afterEach(function() {
                Backbone.history.stop();
            });

            it('can render the "Teams" tab', function() {
                // Hack to make sure the URL fragments from earlier
                // tests don't interfere with Backbone routing by the
                // teams tab view
                document.location.hash = '';

                initializeTeamsTabFactory();
                expect($('.teams-content').text()).toContain('See all teams in your course, organized by topic');
            });
        });
    }
);
