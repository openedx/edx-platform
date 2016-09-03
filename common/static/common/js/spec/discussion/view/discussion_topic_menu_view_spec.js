/* globals DiscussionTopicMenuView, DiscussionSpecHelper, DiscussionCourseSettings */
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
                this.defaultTextWidth = this.completeText.length;
            };

            this.openMenu = function() {
                var menuWrapper = this.view.$('.topic-menu-wrapper');
                expect(menuWrapper).toBeHidden();
                this.view.$el.find('.post-topic-button').first().click();
                expect(menuWrapper).toBeVisible();
            };

            this.closeMenu = function() {
                var menuWrapper = this.view.$('.topic-menu-wrapper');
                expect(menuWrapper).toBeVisible();
                this.view.$el.find('.post-topic-button').first().click();
                expect(menuWrapper).toBeHidden();
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
            this.parentCategoryText = 'Basic Question Types';
            this.selectedOptionText = 'Selection From Options';
            this.completeText = this.parentCategoryText + ' / ' + this.selectedOptionText;
        });

        it('completely show parent category and sub-category', function() {
            var dropdownText;
            this.createTopicView();
            this.view.maxNameWidth = this.defaultTextWidth + 1;
            this.view.$el.find('.topic-menu-entry').first().click();
            dropdownText = this.view.$el.find('.js-selected-topic').text();
            expect(this.completeText).toEqual(dropdownText);
        });

        it('truncation happens with specific title lengths', function() {
            var dropdownText;
            this.createTopicView();
            this.view.$el.find('.topic-menu-entry')[2].click();
            dropdownText = this.view.$el.find('.js-selected-topic').text();
            expect(dropdownText).toEqual('…/Very long category name');

            this.view.$el.find('.topic-menu-entry')[5].click();
            dropdownText = this.view.$el.find('.js-selected-topic').text();
            expect(dropdownText).toEqual('… / What Are Your Goals f …');
        });

        it('truncation happens with longer title lengths', function() {
            var dropdownText;
            this.createTopicView();
            this.view.$el.find('.topic-menu-entry')[3].click();
            dropdownText = this.view.$el.find('.js-selected-topic').text();
            expect(dropdownText).toEqual('… / Very very very very l …');
        });

        it('titles are escaped before display', function() {
            var dropdownText;
            this.createTopicView();
            this.view.$el.find('.topic-menu-entry')[4].click();
            dropdownText = this.view.$el.find('.js-selected-topic').text();
            expect(dropdownText).toContain('em&gt;');
        });

        it('broken span doesn\'t occur', function() {
            var dropdownText;
            this.createTopicView();
            this.view.maxNameWidth = this.selectedOptionText.length + 100;
            this.view.$el.find('.topic-title').first().click();
            dropdownText = this.view.$el.find('.js-selected-topic').text();
            expect(dropdownText.indexOf('/ span>')).toEqual(-1);
        });

        it('appropriate topic is selected if `topicId` is passed', function() {
            var completeText = this.parentCategoryText + ' / Numerical Input',
                dropdownText;
            this.createTopicView({
                topicId: 'c49f0dfb8fc94c9c8d9999cc95190c56'
            });
            this.view.maxNameWidth = this.defaultTextWidth + 1;
            this.view.render();
            dropdownText = this.view.$el.find('.js-selected-topic').text();
            expect(completeText).toEqual(dropdownText);
        });

        it('click outside of the dropdown close it', function() {
            this.createTopicView();
            this.openMenu();
            $(document.body).click();
            expect(this.view.$('.topic-menu-wrapper')).toBeHidden();
        });

        it('can toggle the menu', function() {
            this.createTopicView();
            this.openMenu();
            this.closeMenu();
        });
    });
}).call(this);
