define(['jquery',
        'underscore',
        'moment-with-locales',
        'teams/js/views/team_card',
        'teams/js/models/team'],
    function($, _, moment, TeamCardView, Team) {
        'use strict';

        describe('TeamCardView', function() {
            var createTeamCardView, view;
            createTeamCardView = function() {
                var model = new Team({
                        id: 'test-team',
                        name: 'Test Team',
                        is_active: true,
                        course_id: 'test/course/id',
                        topic_id: 'test-topic',
                        description: 'A team for testing',
                        last_activity_at: '2015-08-21T18:53:01.145Z',
                        country: 'us',
                        language: 'en',
                        membership: []
                    }),
                    TeamCardClass = TeamCardView.extend({
                        maxTeamSize: '100',
                        srInfo: {
                            id: 'test-sr-id',
                            text: 'Screenreader text'
                        },
                        countries: {us: 'United States of America'},
                        languages: {en: 'English'}
                    });
                return new TeamCardClass({
                    model: model
                });
            };

            beforeEach(function() {
                moment.locale('en');
                view = createTeamCardView();
                view.render();
            });

            it('can render itself', function() {
                expect(view.$el).toHaveClass('list-card');
                expect(view.$el.find('.card-title').text()).toContain('Test Team');
                expect(view.$el.find('.card-description').text()).toContain('A team for testing');
                expect(view.$el.find('.team-activity abbr').attr('title')).toContain('August 21st 2015');
                expect(view.$el.find('.team-activity').text()).toContain('Last activity');
                expect(view.$el.find('.card-meta').text()).toContain('0 / 100 Members');
                expect(view.$el.find('.team-location').text()).toContain('United States of America');
                expect(view.$el.find('.team-language').text()).toContain('English');
            });

            it('navigates to the associated team page when its action button is clicked', function() {
                expect(view.$('.action').attr('href')).toEqual('#teams/test-topic/test-team');
            });

            describe('Profile Image Thumbnails', function() {
                /**
                 * Takes an array of objects representing team
                 * members, each having the keys 'username',
                 * 'image_url', and 'last_activity', and sets the
                 * teams membership accordingly and re-renders the
                 * view.
                 */
                var setMemberships, expectThumbnailsOrder;

                setMemberships = function(memberships) {
                    view.model.set({
                        membership: _.map(memberships, function(m) {
                            return {
                                user: {username: m.username, profile_image: {image_url_small: m.image_url}},
                                last_activity_at: m.last_activity
                            };
                        })
                    });
                    view.render();
                };

                /**
                 * Takes an array of objects representing team
                 * members, each having the keys 'username' and
                 * 'image_url', and expects that the image thumbnails
                 * rendered on the team card match, in order, the
                 * members of the provided list.
                 */
                expectThumbnailsOrder = function(members) {
                    var thumbnails = view.$('.item-member-thumb img');
                    expect(thumbnails.length).toBe(members.length);
                    thumbnails.each(function(index, imgEl) {
                        expect(thumbnails.eq(index).attr('alt')).toBe(members[index].username);
                        expect(thumbnails.eq(index).attr('src')).toBe(members[index].image_url);
                    });
                };

                it('displays no thumbnails for an empty team', function() {
                    view.model.set({membership: []});
                    view.render();
                    expect(view.$('.item-member-thumb').length).toBe(0);
                });

                it('displays thumbnails for a nonempty team', function() {
                    var users = [
                        {
                            username: 'user_1', image_url: 'user_1_image',
                            last_activity: new Date('2010/1/1').toString()
                        }, {
                            username: 'user_2', image_url: 'user_2_image',
                            last_activity: new Date('2011/1/1').toString()
                        }
                    ];
                    setMemberships(users);
                    expectThumbnailsOrder([
                        {username: 'user_2', image_url: 'user_2_image'},
                        {username: 'user_1', image_url: 'user_1_image'}
                    ]);
                });

                it('displays thumbnails and an ellipsis for a team with greater than 5 members', function() {
                    var users = [
                        {
                            username: 'user_1', image_url: 'user_1_image',
                            last_activity: new Date('2001/1/1').toString()
                        }, {
                            username: 'user_2', image_url: 'user_2_image',
                            last_activity: new Date('2006/1/1').toString()
                        }, {
                            username: 'user_3', image_url: 'user_3_image',
                            last_activity: new Date('2003/1/1').toString()
                        }, {
                            username: 'user_4', image_url: 'user_4_image',
                            last_activity: new Date('2002/1/1').toString()
                        }, {
                            username: 'user_5', image_url: 'user_5_image',
                            last_activity: new Date('2005/1/1').toString()
                        }, {
                            username: 'user_6', image_url: 'user_6_image',
                            last_activity: new Date('2004/1/1').toString()
                        }
                    ];
                    setMemberships(users);
                    expectThumbnailsOrder([
                        {username: 'user_2', image_url: 'user_2_image'},
                        {username: 'user_5', image_url: 'user_5_image'},
                        {username: 'user_6', image_url: 'user_6_image'},
                        {username: 'user_3', image_url: 'user_3_image'},
                        {username: 'user_4', image_url: 'user_4_image'}
                    ]);
                    expect(view.$('.item-member-thumb').eq(-1)).toHaveText('and others…');
                });
            });
        });
    }
);
