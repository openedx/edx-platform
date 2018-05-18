/* globals Discussion, DiscussionCourseSettings, DiscussionSpecHelper, DiscussionUtil, NewPostView */
(function() {
    'use strict';

    describe('NewPostView', function() {
        var checkVisibility;
        beforeEach(function() {
            DiscussionSpecHelper.setUpGlobals();
            DiscussionSpecHelper.setUnderscoreFixtures();
            window.$$course_id = 'edX/999/test';
            spyOn(DiscussionUtil, 'makeWmdEditor').and.callFake(function($content, $local, cls_identifier) {
                return $local('.' + cls_identifier).html('<textarea></textarea>');
            });
            this.discussion = new Discussion([], {
                pages: 1
            });
        });
        checkVisibility = function(view, expectedVisible, expectedDisabled, render) {
            var disabled, group_disabled;
            if (render) {
                view.render();
            }
            expect(view.$('.group-selector-wrapper').is(':visible') || false).toEqual(expectedVisible);
            disabled = view.$('.js-group-select').prop('disabled') || false;
            group_disabled = view.$('.group-selector-wrapper').hasClass('disabled');
            if (expectedVisible && !expectedDisabled) {
                expect(disabled).toEqual(false);
                return expect(group_disabled).toEqual(false);
            } else if (expectedDisabled) {
                expect(disabled).toEqual(true);
                return expect(group_disabled).toEqual(true);
            }
        };
        describe('group selector', function() {
            beforeEach(function() {
                this.course_settings = new DiscussionCourseSettings({
                    category_map: {
                        children: [['Topic', 'entry'], ['General', 'entry'], ['Not Cohorted', 'entry']],
                        entries: {
                            Topic: {
                                is_divided: true,
                                id: 'topic'
                            },
                            General: {
                                is_divided: true,
                                id: 'general'
                            },
                            'Not Cohorted': {
                                is_divided: false,
                                id: 'not-cohorted'
                            }
                        }
                    },
                    allow_anonymous: false,
                    allow_anonymous_to_peers: false,
                    is_discussion_division_enabled: true,
                    groups: [
                        {
                            id: 1,
                            name: 'Cohort1'
                        }, {
                            id: 2,
                            name: 'Cohort2'
                        }
                    ]
                });
                this.view = new NewPostView({
                    el: $('#fixture-element'),
                    collection: this.discussion,
                    course_settings: this.course_settings,
                    is_commententable_cohorted: true,
                    mode: 'tab'
                });
            });
            it('is not visible to students', function() {
                return checkVisibility(this.view, false, false, true);
            });
            it('allows TAs to see the group selector when the topic is divided', function() {
                DiscussionSpecHelper.makeTA();
                return checkVisibility(this.view, true, false, true);
            });
            it('allows moderators to see the group selector when the topic is divided', function() {
                DiscussionSpecHelper.makeModerator();
                return checkVisibility(this.view, true, false, true);
            });
            it('only enables the group selector when applicable', function() {
                DiscussionSpecHelper.makeModerator();
                checkVisibility(this.view, true, false, true);

                $('option:contains(Not Cohorted)').prop('selected', true);
                $('.post-topic').trigger('change');
                checkVisibility(this.view, true, true, false);

                $('option:contains(Topic)').prop('selected', true);
                $('.post-topic').trigger('change');
                return checkVisibility(this.view, true, false, false);
            });
            it('visibility message changes when group is changed', function() {
                DiscussionSpecHelper.makeModerator();
                checkVisibility(this.view, true, false, true);

                $('option:contains(Topic)').prop('selected', true);
                $('.post-topic').trigger('change');
                expect($('.js-group-select option:selected').text())
                    .toEqual('All Groups');
                expect($('.group-visibility').text().trim())
                    .toEqual('This post will be visible only to All Groups.');

                $('.js-group-select option:contains(Cohort1)').prop('selected', true);
                $('.js-group-select').trigger('change');
                expect($('.js-group-select option:selected').text())
                    .toEqual('Cohort1');
                expect($('.group-visibility').text().trim())
                    .toEqual('This post will be visible only to Cohort1.');
                return checkVisibility(this.view, true, false, false);
            });
            it('allows the user to make a group selection', function() {
                var expectedGroupId,
                    self = this;
                DiscussionSpecHelper.makeModerator();
                this.view.render();
                expectedGroupId = null;
                DiscussionSpecHelper.makeAjaxSpy(function(params) {
                    expect(params.data.group_id).toEqual(expectedGroupId);
                });
                return _.each(['1', '2', ''], function(groupIdStr) {
                    expectedGroupId = groupIdStr;
                    self.view.$('.js-group-select').val(groupIdStr);
                    self.view.$('.js-post-title').val('dummy title');
                    self.view.$('.js-post-body textarea').val('dummy body');
                    self.view.$('.forum-new-post-form').submit();
                    expect($.ajax).toHaveBeenCalled();
                    self.view.$('.forum-new-post-form').prop('disabled', false);
                    return $.ajax.calls.reset();
                });
            });
        });
        describe('always divide inline discussions ', function() {
            beforeEach(function() {
                this.course_settings = new DiscussionCourseSettings({
                    category_map: {
                        children: [],
                        entries: {}
                    },
                    allow_anonymous: false,
                    allow_anonymous_to_peers: false,
                    is_discussion_division_enabled: true,
                    groups: [
                        {
                            id: 1,
                            name: 'Cohort1'
                        }, {
                            id: 2,
                            name: 'Cohort2'
                        }
                    ]
                });
                this.view = new NewPostView({
                    el: $('#fixture-element'),
                    collection: this.discussion,
                    course_settings: this.course_settings,
                    mode: 'tab'
                });
            });
            it('disables the group menu if it is set false', function() {
                DiscussionSpecHelper.makeModerator();
                this.view.is_commentable_divided = false;
                return checkVisibility(this.view, true, true, true);
            });
            it('enables the group menu if it is set true', function() {
                DiscussionSpecHelper.makeModerator();
                this.view.is_commentable_divided = true;
                return checkVisibility(this.view, true, false, true);
            });
            it('is not visible to students when set false', function() {
                this.view.is_commentable_divided = false;
                return checkVisibility(this.view, false, false, true);
            });
            it('is not visible to students when set true', function() {
                this.view.is_commentable_divided = true;
                return checkVisibility(this.view, false, false, true);
            });
        });
        describe('cancel post resets form ', function() {
            var checkPostCancelReset;
            beforeEach(function() {
                this.course_settings = new DiscussionCourseSettings({
                    allow_anonymous_to_peers: true,
                    allow_anonymous: true,
                    category_map: {
                        subcategories: {
                            'Week 1': {
                                subcategories: {},
                                children: [
                                    ['Topic-Level Student-Visible Label', 'entry']
                                ],
                                entries: {
                                    'Topic-Level Student-Visible Label': {
                                        sort_key: null,
                                        is_divided: false,
                                        id: '2b3a858d0c884eb4b272dbbe3f2ffddd'
                                    }
                                }
                            }
                        },
                        children: [
                            ['General', 'entry'],
                            ['Week 1', 'subcategory']
                        ],
                        entries: {
                            General: {
                                sort_key: 'General',
                                is_divided: false,
                                id: 'i4x-waqastest-waqastest-course-waqastest'
                            }
                        }
                    }
                });
            });
            checkPostCancelReset = function(mode, discussion, course_settings) {
                var eventSpy, view;
                view = new NewPostView({
                    el: $('#fixture-element'),
                    collection: discussion,
                    course_settings: course_settings,
                    mode: mode
                });
                view.render();
                eventSpy = jasmine.createSpy('eventSpy');
                view.listenTo(view, 'newPost:cancel', eventSpy);
                view.$('.post-errors').html("<li class='post-error'>Title can't be empty</li>");
                view.$("label[for$='post-type-question']").click();
                view.$('.js-post-title').val('Test Title');
                view.$('.js-post-body textarea').val('Test body');
                view.$('.wmd-preview p').html('Test body');
                view.$('input[name=follow]').prop('checked', false);
                view.$('input[name=anonymous]').prop('checked', true);
                view.$('input[name=anonymous_to_peers]').prop('checked', true);
                if (mode === 'tab') {
                    view.$("a[data-discussion-id='2b3a858d0c884eb4b272dbbe3f2ffddd']").click();
                }
                view.$('.cancel').click();
                expect(eventSpy).toHaveBeenCalled();
                expect(view.$('.post-errors').html()).toEqual('');
                expect($("input[id$='post-type-discussion']")).toBeChecked();
                expect($("input[id$='post-type-question']")).not.toBeChecked();
                expect(view.$('.js-post-title').val()).toEqual('');
                expect(view.$('.js-post-body textarea').val()).toEqual('');
                expect(view.$('input[name=follow]')).toBeChecked();
                expect(view.$('input[name=anonymous]')).not.toBeChecked();
                expect(view.$('input[name=anonymous_to_peers]')).not.toBeChecked();
                if (mode === 'tab') {
                    return expect(view.$('.post-topic option:selected').text()).toEqual('General');
                }
            };
            return _.each(['tab', 'inline'], function(mode) {
                it('resets the form in ' + mode + ' mode', function() {
                    return checkPostCancelReset(mode, this.discussion, this.course_settings);
                });
            });
        });
        describe('default topic ', function() {
            beforeEach(function() {
                this.course_settings = new DiscussionCourseSettings({
                    allow_anonymous_to_peers: true,
                    allow_anonymous: true,
                    category_map: {
                        subcategories: {
                            'Week 1': {
                                subcategories: {},
                                children: [
                                    ['Topic-Level Student-Visible Label', 'entry']
                                ],
                                entries: {
                                    'Topic-Level Student-Visible Label': {
                                        sort_key: null,
                                        is_divided: false,
                                        id: '2b3a858d0c884eb4b272dbbe3f2ffddd'
                                    }
                                }
                            }
                        },
                        children: [
                            ['First topic', 'entry'],
                            ['Week 1', 'subcategory']
                        ],
                        entries: {
                            'First topic': {
                                sort_key: 'First topic',
                                is_divided: false,
                                id: 'i4x-waqastest-waqastest-course-waqastest'
                            }
                        }
                    }
                });
            });

            it('should be the first topic if General is not found', function() {
                var eventSpy, view;
                view = new NewPostView({
                    el: $('#fixture-element'),
                    collection: this.discussion,
                    course_settings: this.course_settings,
                    mode: 'tab'
                });
                view.render();
                eventSpy = jasmine.createSpy('eventSpy');
                view.listenTo(view, 'newPost:cancel', eventSpy);
                view.$('.post-errors').html("<li class='post-error'>Title can't be empty</li>");
                view.$("label[for$='post-type-question']").click();
                view.$('.js-post-title').val('Test Title');
                view.$('.js-post-body textarea').val('Test body');
                view.$('.wmd-preview p').html('Test body');
                view.$('input[name=follow]').prop('checked', false);
                view.$('input[name=anonymous]').prop('checked', true);
                view.$('input[name=anonymous_to_peers]').prop('checked', true);
                view.$("a[data-discussion-id='2b3a858d0c884eb4b272dbbe3f2ffddd']").click();
                view.$('.cancel').click();
                expect(view.$('.post-topic option:selected').text()).toEqual('First topic');
            });
        });
        it('posts to the correct URL', function() {
            var topicId, view;
            topicId = 'test_topic';
            spyOn($, 'ajax').and.callFake(function(params) {
                expect(params.url.path()).toEqual(DiscussionUtil.urlFor('create_thread', topicId));
                return {
                    always: function() {
                    }
                };
            });
            view = new NewPostView({
                el: $('#fixture-element'),
                collection: this.discussion,
                course_settings: new DiscussionCourseSettings({
                    allow_anonymous: false,
                    allow_anonymous_to_peers: false
                }),
                mode: 'inline',
                topicId: topicId
            });
            view.render();
            view.$('.forum-new-post-form').submit();
            return expect($.ajax).toHaveBeenCalled();
        });
    });
}).call(this);
