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
                this.defaultTextWidth = this.view.getNameWidth(this.completeText);
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
                            'children': ['Selection From Options', 'Numerical Input'],
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
                                }
                            }
                        }
                    },
                    'children': ['Basic Question Types'],
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
          this.view.$el.find('a.topic-title').first().click();
          dropdownText = this.view.$el.find('.js-selected-topic').text();
          expect(this.completeText).toEqual(dropdownText);
        });

        it('completely show just sub-category', function() {
            var dropdownText;
            this.createTopicView();
            this.view.maxNameWidth = this.defaultTextWidth - 10;
            this.view.$el.find('a.topic-title').first().click();
            dropdownText = this.view.$el.find('.js-selected-topic').text();
            expect(dropdownText.indexOf('…')).toEqual(0);
            expect(dropdownText).toContain(this.selectedOptionText);
        });

        it('partially show sub-category', function() {
            this.createTopicView();
            var parentWidth = this.view.getNameWidth(this.parentCategoryText),
                dropdownText;
            this.view.maxNameWidth = this.defaultTextWidth - parentWidth;
            this.view.$el.find('a.topic-title').first().click();
            dropdownText = this.view.$el.find('.js-selected-topic').text();
            expect(dropdownText.indexOf('…')).toEqual(0);
            expect(dropdownText.lastIndexOf('…')).toBeGreaterThan(0);
        });

        it('broken span doesn\'t occur', function() {
            var dropdownText;
            this.createTopicView();
            this.view.maxNameWidth = this.view.getNameWidth(this.selectedOptionText) + 100;
            this.view.$el.find('a.topic-title').first().click();
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
