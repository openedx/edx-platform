/* globals DiscussionTopicMenuView, DiscussionSpecHelper, DiscussionCourseSettings, _ */
(function() {
    'use strict';
    describe('DiscussionTopicMenuView', function() {
        beforeEach(function() {
            this.createTopicView = function(options) {
                options = _.extend({
                    course_settings: this.course_settings,
                    topicId: void 0
                }, options);
                this.view = new DiscussionTopicMenuView(options);
                this.view.render().appendTo('#fixture-element');
            };

            DiscussionSpecHelper.setUpGlobals();
            DiscussionSpecHelper.setUnderscoreFixtures();
            this.course_settings = new DiscussionCourseSettings({
                'category_map': {
                    'subcategories': {
                        'Basic Question Types': {
                            'subcategories': {},
                            'children': [
                                'Selection From Options',
                                'Numerical Input',
                                'Very long category name',
                                'Very very very very long category name',
                                'Name with <em>HTML</em>'
                            ],
                            'entries': {
                                'Selection From Options': {
                                    'sort_key': null,
                                    'is_cohorted': true,
                                    'id': 'cba3e4cd91d0466b9ac50926e495b76f'
                                },
                                'Numerical Input': {
                                    'sort_key': null,
                                    'is_cohorted': false,
                                    'id': 'c49f0dfb8fc94c9c8d9999cc95190c56'
                                },
                                'Very long category name': {
                                    'sort_key': null,
                                    'is_cohorted': false,
                                    'id': 'c49f0dfb8fc94c9c8d9999cc95190c59'
                                },
                                'Very very very very long category name': {
                                    'sort_key': null,
                                    'is_cohorted': false,
                                    'id': 'c49f0dfb8fc94c9c8d9999cc95190e32'
                                },
                                'Name with <em>HTML</em>': {
                                    'sort_key': null,
                                    'is_cohorted': false,
                                    'id': 'c49f0dfb8fc94c9c8d9999cc95190363'
                                }

                            }
                        },
                        'Example Inline Discussion': {
                            'subcategories': {},
                            'children': [
                                'What Are Your Goals for Creating a MOOC?'
                            ],
                            'entries': {
                                'What Are Your Goals for Creating a MOOC?': {
                                    'sort_key': null,
                                    'is_cohorted': true,
                                    'id': 'cba3e4cd91d0466b9ac50926e495b931'
                                }
                            }
                        }
                    },
                    'children': ['Basic Question Types', 'Example Inline Discussion'],
                    'entries': {}
                },
                'is_cohorted': true
            });
        });

        it('defaults to first subtopic', function() {
            this.createTopicView();
            expect(this.view.$el.find('option.topic-title:selected').text()).toEqual('Selection From Options');
        });

        it('titles are escaped before display', function() {
            this.createTopicView();
            $(this.view.$el.find('option.topic-title')[4]).prop('selected', true);
            expect(this.view.$el.find('option.topic-title:selected').text()).toContain('<em>');
        });

        it('appropriate topic is selected if `topicId` is passed', function() {
            this.createTopicView({
                topicId: 'c49f0dfb8fc94c9c8d9999cc95190c56'
            });
            this.view.render();
            expect(this.view.$el.find('option.topic-title:selected').text()).toEqual('Numerical Input');
        });
    });
}).call(this);
