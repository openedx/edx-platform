define(["jquery", "backbone", "teams/js/teams_tab_factory"],
    function($, Backbone, TeamsTabFactory) {
        'use strict';
       
        describe("Teams Tab Factory", function() {
            var teamsTab;

            beforeEach(function() {
                setFixtures('<section class="teams-content"></section>');
                teamsTab = new TeamsTabFactory({
                    topics: {results: []},
                    topicsUrl: '',
                    teamsUrl: '',
                    maxTeamSize: 9999,
                    courseID: 'edX/DemoX/Demo_Course'
                });
            });

            afterEach(function() {
                Backbone.history.stop();
            });

            it("can load templates", function() {
                expect($("body").text()).toContain("My Teams");
                expect($("body").text()).toContain("Showing 0 out of 0 total");
            });

            it("displays a header", function() {
                expect($("body").html()).toContain("See all teams in your course, organized by topic");
            });
        });
    }
);
