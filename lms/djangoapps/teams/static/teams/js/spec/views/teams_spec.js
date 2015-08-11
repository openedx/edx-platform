define([
    'backbone',
    'teams/js/collections/team',
    'teams/js/collections/team_membership',
    'teams/js/views/teams'
], function (Backbone, TeamCollection, TeamMembershipCollection, TeamsView) {
    'use strict';
    describe('Teams View', function () {
        var teamsView, teamCollection, initialTeams,
            initialTeamMemberships, teamMembershipCollection;

        var createTeams = function (startIndex, stopIndex) {
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
            },
            countries = [
                ['', ''],
                ['US', 'United States'],
                ['CA', 'Canada'],
                ['MX', 'Mexico']
            ],
            languages = [
                ['', ''],
                ['en', 'English'],
                ['es', 'Spanish'],
                ['fr', 'French']
            ];

        var createTeamMemberships = function(startIndex, stopIndex) {
            var teams = createTeams(startIndex, stopIndex)
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

        var verifyCards = function(view, teams) {
            var teamCards = view.$('.team-card');
            _.each(teams, function (team, index) {
                var currentCard = teamCards.eq(index);
                expect(currentCard.text()).toMatch(team.name);
                expect(currentCard.text()).toMatch(_.object(languages)[team.language]);
                expect(currentCard.text()).toMatch(_.object(countries)[team.country]);
            });

        }

        beforeEach(function () {
            setFixtures('<div class="teams-container"></div>');
            initialTeams = createTeams(1, 5);
            teamCollection = new TeamCollection(
                {
                    count: 6,
                    num_pages: 2,
                    current_page: 1,
                    start: 0,
                    results: initialTeams
                },
                {
                    course_id: 'my/course/id',
                    parse: true
                }
            );

            initialTeamMemberships = createTeamMemberships(1, 5);
            teamMembershipCollection = new TeamMembershipCollection(
                {
                    count: 11,
                    num_pages: 3,
                    current_page: 1,
                    start: 0,
                    results: initialTeamMemberships
                },
                {
                    course_id: 'my/course/id',
                    parse: true,
                    url: 'api/teams/team_memberships',
                    username: 'andya',
                }
            );
        });

        it('can render itself with teams collection', function () {
            teamsView = new TeamsView({
                el: '.teams-container',
                collection: teamCollection,
                teamParams: {
                    countries: countries,
                    languages: languages
                }
            }).render();

            expect(teamsView.$('.teams-paging-header').text()).toMatch('Showing 1-5 out of 6 total');

            var footerEl = teamsView.$('.teams-paging-footer');
            expect(footerEl.text()).toMatch('1\\s+out of\\s+\/\\s+2');
            expect(footerEl).not.toHaveClass('hidden');

            verifyCards(teamsView, initialTeams);
        });

        it('can render itself with team memberships collection', function () {
            teamsView = new TeamsView({
                el: '.teams-container',
                collection: teamMembershipCollection,
                teamParams: {}
            }).render();

            expect(teamsView.$('.teams-paging-header').text()).toMatch('Showing 1-5 out of 11 total');
            var footerEl = teamsView.$('.teams-paging-footer');
            expect(footerEl.text()).toMatch('1\\s+out of\\s+\/\\s+3');
            expect(footerEl).not.toHaveClass('hidden');

            verifyCards(teamsView, initialTeamMemberships);
        });

        it ('can render the actions view', function () {
            teamsView = new TeamsView({
                el: '.teams-container',
                collection: teamCollection,
                teamParams: {},
            }).render();

            expect(teamsView.$el.text()).not.toContain(
                'Are you having trouble finding a team to join?'
            );

            teamsView = new TeamsView({
                el: '.teams-container',
                collection: teamCollection,
                teamParams: {},
                showActions: true
            }).render();

            expect(teamsView.$el.text()).toContain(
                'Are you having trouble finding a team to join?'
            );
        });
    });
});
