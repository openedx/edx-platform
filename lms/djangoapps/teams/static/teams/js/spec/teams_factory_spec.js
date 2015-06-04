define(["jquery", "teams/js/teams_tab_factory"],
    function($, TeamsTabFactory) {
        'use strict';
       
        describe("teams django app", function() {
            var teamsTab;

            beforeEach(function() {
                setFixtures('<section class="teams-content"></section>');
                teamsTab = new TeamsTabFactory();
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
