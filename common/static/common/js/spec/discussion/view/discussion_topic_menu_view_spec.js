/* globals DiscussionTopicMenuView, DiscussionSpecHelper, DiscussionCourseSettings, _ */
(function() {
    'use strict';
    describe('DiscussionTopicMenuView', function() {
        var ExpectedDiscussionId;
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
                category_map: {
                    subcategories: {
                        'Basic Question Types': {
                            subcategories: {},
                            children: [
                                ['Selection From Options', 'entry'],
                                ['Numerical Input', 'entry'],
                                ['Very long category name', 'entry'],
                                ['Very very very very long category name', 'entry'],
                                ['Name with <em>HTML</em>', 'entry']
                            ],
                            entries: {
                                'Selection From Options': {
                                    sort_key: null,
                                    is_divided: true,
                                    id: 'cba3e4cd91d0466b9ac50926e495b76f'
                                },
                                'Numerical Input': {
                                    sort_key: null,
                                    is_divided: false,
                                    id: 'c49f0dfb8fc94c9c8d9999cc95190c56'
                                },
                                'Very long category name': {
                                    sort_key: null,
                                    is_divided: false,
                                    id: 'c49f0dfb8fc94c9c8d9999cc95190c59'
                                },
                                'Very very very very long category name': {
                                    sort_key: null,
                                    is_divided: false,
                                    id: 'c49f0dfb8fc94c9c8d9999cc95190e32'
                                },
                                'Name with <em>HTML</em>': {
                                    sort_key: null,
                                    is_divided: false,
                                    id: 'c49f0dfb8fc94c9c8d9999cc95190363'
                                }

                            }
                        },
                        'Example Inline Discussion': {
                            subcategories: {},
                            children: [
                                ['What Are Your Goals for Creating a MOOC?', 'entry']
                            ],
                            entries: {
                                'What Are Your Goals for Creating a MOOC?': {
                                    sort_key: null,
                                    is_divided: true,
                                    id: 'cba3e4cd91d0466b9ac50926e495b931'
                                }
                            }
                        }
                    },
                    children: [
                        ['Basic Question Types', 'subcategory'],
                        ['Example Inline Discussion', 'subcategory']
                    ],
                    entries: {}
                },
                is_cohorted: true
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

        it('appropriate topic is selected if topicId is passed', function() {
            this.createTopicView({
                topicId: 'c49f0dfb8fc94c9c8d9999cc95190c56'
            });
            this.view.render();
            expect(this.view.$el.find('option.topic-title:selected').text()).toEqual('Numerical Input');
        });
        it('if general topic is not present then topiId is set to first discussion topicId', function() {
            this.createTopicView({});
            this.view.render();
            ExpectedDiscussionId = this.view.$('.post-topic option').first().data('discussion-id');
            expect(this.view.getCurrentTopicId()).toEqual(ExpectedDiscussionId);
        });
    });
}).call(this);
