define([
    'backbone',
    'teams/js/collections/team',
    'teams/js/collections/team_membership',
    'teams/js/views/teams'
], function (Backbone, TeamCollection, TeamMembershipCollection, TeamsView) {
    'use strict';
    describe('Teams View', function () {
        var countries = [
            ['', ''],
            ['US', 'United States'],
            ['CA', 'Canada'],
            ['MX', 'Mexico']
        ];
        var languages = [
            ['', ''],
            ['en', 'English'],
            ['es', 'Spanish'],
            ['fr', 'French']
        ];

        var createTeamData = function (startIndex, stopIndex) {
            return _.map(_.range(startIndex, stopIndex + 1), function (i) {
                return {
                    name: "team " + i,
                    id: "id " + i,
                    language: languages[i%4][0],
                    country: countries[i%4][0],
                    is_active: true,
                    membership: []
                };
            });
        };

        var createTeams = function(teamData) {
            return new TeamCollection(
                {
                    count: 6,
                    num_pages: 2,
                    current_page: 1,
                    start: 0,
                    results: teamData
                },
                {
                    course_id: 'my/course/id',
                    parse: true
                }
            );
        };

        var createTeamMembershipsData = function(startIndex, stopIndex) {
            var teams = createTeamData(startIndex, stopIndex);
            return _.map(_.range(startIndex, stopIndex + 1), function (i) {
                return {
                    user: {
                        'username': 'andya',
                        'url': 'https://openedx.example.com/api/user/v1/accounts/andya'
                    },
                    team: teams[i-1]
                };
            });
        };

        var createTeamMemberships = function(teamMembershipData, options) {
            return new TeamMembershipCollection(
                {
                    count: 11,
                    num_pages: 3,
                    current_page: 1,
                    start: 0,
                    results: teamMembershipData
                },
                _.extend(_.extend({}, {
                        course_id: 'my/course/id',
                        parse: true,
                        url: 'api/teams/team_memberships',
                        username: 'andya',
                        privileged: false
                    }),
                    options)
            );
        };

        var verifyCards = function(view, teams) {
            var teamCards = view.$('.team-card');
            _.each(teams, function (team, index) {
                var currentCard = teamCards.eq(index);
                expect(currentCard.text()).toMatch(team.name);
                expect(currentCard.text()).toMatch(_.object(languages)[team.language]);
                expect(currentCard.text()).toMatch(_.object(countries)[team.country]);
            });
        };

        var createTeamsView = function(options) {
            return new TeamsView({
                el: '.teams-container',
                collection: options.teams || createTeams(createTeamData(1, 5)),
                teamMemberships: options.teamMemberships || createTeamMemberships(createTeamMembershipsData(1, 5)),
                teamParams: {
                    topicID: 'test-topic',
                    countries: countries,
                    languages: languages
                }
            }).render();
        };

        beforeEach(function () {
            setFixtures('<div class="teams-container"></div>');
        });

        it('can render itself with team collection', function () {
            var testTeamData = createTeamData(1, 5),
                teamsView = createTeamsView({
                    teams: createTeams(testTeamData)
                });

            expect(teamsView.$('.teams-paging-header').text()).toMatch('Showing 1-5 out of 6 total');

            var footerEl = teamsView.$('.teams-paging-footer');
            expect(footerEl.text()).toMatch('1\\s+out of\\s+\/\\s+2');
            expect(footerEl).not.toHaveClass('hidden');

            verifyCards(teamsView, testTeamData);
        });

        it('can render itself with team membership collection', function () {
            var teamMembershipsData = createTeamMembershipsData(1, 5),
                teamMemberships = createTeamMemberships(teamMembershipsData),
                teamsView = createTeamsView({
                    teams: teamMemberships,
                    teamMemberships: teamMemberships
                });

            expect(teamsView.$('.teams-paging-header').text()).toMatch('Showing 1-5 out of 11 total');
            var footerEl = teamsView.$('.teams-paging-footer');
            expect(footerEl.text()).toMatch('1\\s+out of\\s+\/\\s+3');
            expect(footerEl).not.toHaveClass('hidden');

            verifyCards(teamsView, teamMembershipsData);
        });

        describe("Team Actions View", function() {
            it('can render itself correctly', function () {
                var emptyMembership = createTeamMemberships([]),
                    teamsView = createTeamsView({ teamMemberships: emptyMembership });
                expect(teamsView.$('.title').text()).toBe('Are you having trouble finding a team to join?');
                expect(teamsView.$('.copy').text()).toBe(
                    "Try browsing all teams or searching team descriptions. If you " +
                    "still can't find a team to join, create a new team in this topic."
                );
            });


            it('can navigate to correct routes', function () {
                var emptyMembership = createTeamMemberships([]),
                    teamsView = createTeamsView({ teamMemberships: emptyMembership });
                spyOn(Backbone.history, 'navigate');
                teamsView.$('a.browse-teams').click();
                expect(Backbone.history.navigate.calls[0].args).toContain('browse');

                teamsView.$('a.search-teams').click();
                // TODO! Should be updated once team description search feature is available
                expect(Backbone.history.navigate.calls[1].args).toContain('browse');

                teamsView.$('a.create-team').click();
                expect(Backbone.history.navigate.calls[2].args).toContain('topics/test-topic/create-team');
            });

            it('does not show for a user already in a team', function () {
                var teamsView = createTeamsView({});
                expect(teamsView.$el.text()).not.toContain(
                    'Are you having trouble finding a team to join?'
                );
            });

            it('shows for a privileged user already in a team', function () {
                var staffMembership = createTeamMemberships(
                        createTeamMembershipsData(1, 5),
                        { privileged: true }
                    ),
                    teamsView = createTeamsView({ teamMemberships: staffMembership });
                expect(teamsView.$el.text()).toContain(
                    'Are you having trouble finding a team to join?'
                );
            });
        });
    });
});
