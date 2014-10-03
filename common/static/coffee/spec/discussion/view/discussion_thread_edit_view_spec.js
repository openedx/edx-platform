(function() {
    'use strict';
    describe('DiscussionThreadEditView', function() {
        beforeEach(function() {
            DiscussionSpecHelper.setUpGlobals();
            DiscussionSpecHelper.setUnderscoreFixtures();
            spyOn(DiscussionUtil, 'makeWmdEditor');
            this.threadData = DiscussionViewSpecHelper.makeThreadWithProps();
            this.thread = new Thread(this.threadData);
            this.course_settings = new DiscussionCourseSettings({
                'category_map': {
                    'children': ['Topic'],
                    'entries': {
                        'Topic': {
                            'is_cohorted': true,
                            'id': 'topic'
                        }
                    }
                },
                'is_cohorted': true
            });

            this.createEditView = function (options) {
              options = _.extend({
                    container: $('#fixture-element'),
                    model: this.thread,
                    mode: 'tab',
                    topicId: 'dummy_id',
                    threadType: 'question',
                    course_settings: this.course_settings
                }, options);
                this.view = new DiscussionThreadEditView(options);
                this.view.render();
            };
        });

        it('can save new data correctly', function() {
            var view;
            spyOn($, 'ajax').andCallFake(function(params) {
                expect(params.url.path()).toEqual(DiscussionUtil.urlFor('update_thread', 'dummy_id'));
                expect(params.data.thread_type).toBe('discussion');
                expect(params.data.commentable_id).toBe('topic');
                expect(params.data.title).toBe('new_title');
                params.success();
                return {always: function() {}};
            });
            this.createEditView();
            this.view.$el.find('a.topic-title').first().click(); // set new topic
            this.view.$('.edit-post-title').val('new_title'); // set new title
            this.view.$("label[for$='post-type-discussion']").click(); // set new thread type
            this.view.$('.post-update').click();
            expect($.ajax).toHaveBeenCalled();

            expect(this.thread.get('title')).toBe('new_title');
            expect(this.thread.get('commentable_id')).toBe('topic');
            expect(this.thread.get('thread_type')).toBe('discussion');
            expect(this.thread.get('courseware_title')).toBe('Topic');

            expect(this.view.$('.edit-post-title')).toHaveValue('');
            expect(this.view.$('.wmd-preview p')).toHaveText('');
        });

        it('can close the view', function() {
            this.createEditView();
            this.view.$('.post-cancel').click();
            expect($('.edit-post-form')).not.toExist();
        });
    });
}).call(this);
