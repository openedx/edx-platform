/* globals
    DiscussionCourseSettings, DiscussionSpecHelper, DiscussionThreadEditView, DiscussionUtil,
    DiscussionViewSpecHelper, Thread
*/
(function() {
    'use strict';
    describe('DiscussionThreadEditView', function() {
        var testUpdate, testCancel;

        beforeEach(function() {
            DiscussionSpecHelper.setUpGlobals();
            DiscussionSpecHelper.setUnderscoreFixtures();
            spyOn(DiscussionUtil, 'makeWmdEditor');
            this.threadData = DiscussionViewSpecHelper.makeThreadWithProps({
                'commentable_id': 'test_topic',
                'title': 'test thread title'
            });
            this.thread = new Thread(this.threadData);
            this.course_settings = DiscussionSpecHelper.makeCourseSettings();

            this.createEditView = function(options) {
                options = _.extend({
                    container: $('#fixture-element'),
                    model: this.thread,
                    mode: 'tab',
                    course_settings: this.course_settings
                }, options);
                this.view = new DiscussionThreadEditView(options);
                this.view.render();
            };
        });

        testUpdate = function(view, thread, newTopicId, newTopicName) {
            spyOn($, 'ajax').and.callFake(function(params) {
                expect(params.url.path()).toEqual(DiscussionUtil.urlFor('update_thread', 'dummy_id'));
                expect(params.data.thread_type).toBe('discussion');
                expect(params.data.commentable_id).toBe(newTopicId);
                expect(params.data.title).toBe('changed thread title');
                params.success();
                return {
                    always: function() {
                    }
                };
            });

            view.$el.find('a.topic-title').filter(function(idx, el) {
                return $(el).data('discussionId') === newTopicId;
            }).click(); // set new topic
            view.$('.edit-post-title').val('changed thread title'); // set new title
            view.$("label[for$='post-type-discussion']").click(); // set new thread type
            view.$('.post-update').click();
            expect($.ajax).toHaveBeenCalled();

            expect(thread.get('title')).toBe('changed thread title');
            expect(thread.get('thread_type')).toBe('discussion');
            expect(thread.get('commentable_id')).toBe(newTopicId);
            expect(thread.get('courseware_title')).toBe(newTopicName);
            expect(view.$('.edit-post-title')).toHaveValue('');
            expect(view.$('.wmd-preview p')).toHaveText('');
        };

        it('can save new data correctly in tab mode', function() {
            this.createEditView();
            testUpdate(this.view, this.thread, 'other_topic', 'Other Topic');
        });

        it('can save new data correctly in inline mode', function() {
            this.createEditView({'mode': 'inline'});
            testUpdate(this.view, this.thread, 'other_topic', 'Other Topic');
        });

        testCancel = function(view) {
            view.$('.post-cancel').click();
            expect($('.edit-post-form')).not.toExist();
        };

        it('can close the view in tab mode', function() {
            this.createEditView();
            testCancel(this.view);
        });

        it('can close the view in inline mode', function() {
            this.createEditView({'mode': 'inline'});
            testCancel(this.view);
        });

        describe('renderComments', function() {
            beforeEach(function() {
                this.course_settings = new DiscussionCourseSettings({
                    'category_map': {
                        'children': ['Topic', 'General', 'Basic Question'],
                        'entries': {
                            'Topic': {
                                'is_cohorted': true,
                                'id': 'topic'
                            },
                            'General': {
                                'sort_key': 'General',
                                'is_cohorted': false,
                                'id': '6.00.1x_General'
                            },
                            'Basic Question': {
                                'is_cohorted': false,
                                'id': "6>00'1x\"Basic_Question"
                            }
                        }
                    },
                    'is_cohorted': true
                });
            });

            it('can save new data correctly for current discussion id without dots', function() {
                this.createEditView({topicId: 'topic'});
                testUpdate(this.view, this.thread, '6.00.1x_General', 'General');
            });

            it('can save new data correctly for current discussion id with dots', function() {
                this.createEditView({topicId: '6.00.1x_General'});
                testUpdate(this.view, this.thread, "6>00\'1x\"Basic_Question", 'Basic Question');
            });

            it('can save new data correctly for current discussion id with special characters', function() {
                this.createEditView({topicId: "6>00\'1x\"Basic_Question"});
                testUpdate(this.view, this.thread, '6.00.1x_General', 'General');
            });
        });
    });
}).call(this);
