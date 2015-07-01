define(["jquery", "backbone", "teams/js/teams_tab_factory"],
    function($, Backbone, TeamsTabFactory) {
        'use strict';
       
        describe("Teams tab", function() {
            var teamsTab;

            beforeEach(function() {
                setFixtures('<section class="teams-content"></section>');
                teamsTab = new TeamsTabFactory($(".teams-content"));
            });

            afterEach(function() {
                Backbone.history.stop();
            });

            it("can load templates", function() {
                expect($("body").text()).toContain("This is the new Teams tab");
            });

            it("displays a header", function() {
                expect($("body").html()).toContain("Course teams are organized");
            });
        });
    }
);
