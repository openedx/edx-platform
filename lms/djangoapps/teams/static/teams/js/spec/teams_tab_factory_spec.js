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
                        teamMembershipData: null
                    }
                });
            };

            beforeEach(function() {
                setFixtures('<section class="teams-content"></section>');
            });

            afterEach(function() {
                Backbone.history.stop();
            });

            it("can load templates", function() {
                initializeTeamsTabFactory();
                expect($('.teams-content').text()).toContain("My Teams");
                expect($('.teams-content').text()).toContain("Showing 0 out of 0 total");
            });

            it("displays a header", function() {
                initializeTeamsTabFactory();
                expect($('.teams-content').html()).toContain("See all teams in your course, organized by topic");
            });
        });
    }
);
