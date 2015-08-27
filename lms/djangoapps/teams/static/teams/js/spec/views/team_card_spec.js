define(['jquery',
        'underscore',
        'teams/js/views/team_card',
        'teams/js/models/team'],
    function ($, _, TeamCardView, Team) {
        describe('TeamCardView', function () {
            var createTeamCardView, view;
            createTeamCardView = function () {
                var model = new Team({
                    id: 'test-team',
                    name: 'Test Team',
                    is_active: true,
                    course_id: 'test/course/id',
                    topic_id: 'test-topic',
                    description: 'A team for testing',
                    last_activity_at: "2015-08-21T18:53:01.145Z",
                    country: 'us',
                    language: 'en'
                }),
                    teamCardClass = TeamCardView.extend({
                        maxTeamSize: '100',
                        srInfo: {
                            id: 'test-sr-id',
                            text: 'Screenreader text'
                        },
                        countries: {us: 'United States of America'},
                        languages: {en: 'English'}
                    });
                return new teamCardClass({
                    model: model
                });
            };

            beforeEach(function () {
                view = createTeamCardView();
                view.render();
            });

            it('can render itself', function () {
                expect(view.$el).toHaveClass('list-card');
                expect(view.$el.find('.card-title').text()).toContain('Test Team');
                expect(view.$el.find('.card-description').text()).toContain('A team for testing');
                expect(view.$el.find('.team-activity abbr').attr('title')).toEqual("2015-08-21T18:53:01.145Z");
                expect(view.$el.find('.team-activity').text()).toContain('Last Activity');
                expect(view.$el.find('.card-meta').text()).toContain('0 / 100 Members');
                expect(view.$el.find('.team-location').text()).toContain('United States of America');
                expect(view.$el.find('.team-language').text()).toContain('English');
            });

            it('navigates to the associated team page when its action button is clicked', function () {
                expect(view.$('.action').attr('href')).toEqual('#teams/test-topic/test-team');
            });
        });
    }
);
