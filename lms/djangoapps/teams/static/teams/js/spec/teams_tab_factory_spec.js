define(["jquery", "backbone", "teams/js/teams_tab_factory"],
    function($, Backbone, TeamsTabFactory) {
        'use strict';
       
        describe("Teams Tab Factory", function() {
            var teamsTab;

            var initializeTeamsTabFactory = function() {
                TeamsTabFactory({
                    topics: {results: []},
                    topicsUrl: '',
                    teamsUrl: '',
                    maxTeamSize: 9999,
                    courseID: 'edX/DemoX/Demo_Course',
                    userInfo: {
                        username: 'test-user',
                        privileged: false,
                        staff: false,
                        team_memberships_data: null
                    }
                });
            };

            beforeEach(function() {
                setFixtures('<section class="teams-content"></section>');
            });

            afterEach(function() {
                Backbone.history.stop();
            });

            it('can render the "Teams" tab', function() {
                initializeTeamsTabFactory();
                expect($('.teams-content').text()).toContain('See all teams in your course, organized by topic');
            });
        });
    }
);
