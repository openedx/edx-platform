/* globals
 _, Discussion, DiscussionCourseSettings, DiscussionViewSpecHelper, DiscussionSpecHelper,
 DiscussionInlineView, DiscussionUtil, DiscussionThreadShowView, Thread
 */
(function() {
    'use strict';
    describe('DiscussionInlineView', function() {
        var createTestView, showDiscussion, setNextAjaxResult,
            TEST_THREAD_TITLE = 'Test thread title';

        beforeEach(function() {
            DiscussionSpecHelper.setUpGlobals();
            setFixtures(
                '<div class="discussion-module" data-discussion-id="test-discussion-id"' +
                '  data-user-create-comment="true"' +
                '  data-user-create-subcomment="true"' +
                '  data-read-only="false">' +
                '  <div class="discussion-module-header">' +
                '    <h3 class="discussion-module-title">Test Discussion</h3>' +
                '    <div class="inline-discussion-topic">' +
                '      <span class="inline-discussion-topic-title">Topic:</span> Category / Target ' +
                '    </div>' +
                '  </div>' +
                '  <button class="discussion-show btn btn-brand" data-discussion-id="test-discussion-id">' +
                '     <span class="button-text">Show Discussion</span>' +
                '  </button>' +
                '</div>'
            );
            DiscussionSpecHelper.setUnderscoreFixtures();
            this.ajaxSpy = spyOn($, 'ajax');

            // Don't attempt to render markdown
            spyOn(DiscussionUtil, 'makeWmdEditor');
            spyOn(DiscussionThreadShowView.prototype, 'convertMath');
        });

        createTestView = function() {
            var testView = new DiscussionInlineView({
                el: $('.discussion-module')
            });
            testView.render();
            return testView;
        };

        showDiscussion = function(test, testView) {
            setNextAjaxResult(test, {
                user_info: DiscussionSpecHelper.getTestUserInfo(),
                roles: DiscussionSpecHelper.getTestRoleInfo(),
                course_settings: DiscussionSpecHelper.createTestCourseSettings().attributes,
                discussion_data: DiscussionViewSpecHelper.makeThreadWithProps({
                    commentable_id: 'test-topic',
                    title: TEST_THREAD_TITLE
                }),
                page: 1,
                num_pages: 1
            });
            testView.$('.discussion-show').click();
        };

        setNextAjaxResult = function(test, result) {
            test.ajaxSpy.and.callFake(function(params) {
                var deferred = $.Deferred();
                deferred.resolve();
                params.success(result);
                return deferred;
            });
        };

        describe('inline discussion', function() {
            it('is shown after "Show Discussion" is clicked', function() {
                var testView = createTestView(this),
                    showButton = testView.$('.discussion-show');
                showDiscussion(this, testView);

                // Verify that the discussion is now shown
                expect(showButton).toHaveClass('shown');
                expect(showButton.text().trim()).toEqual('Hide Discussion');
                expect(testView.$('.inline-discussion:visible')).not.toHaveClass('is-hidden');
            });

            it('is hidden after "Hide Discussion" is clicked', function() {
                var testView = createTestView(this),
                    showButton = testView.$('.discussion-show');
                showDiscussion(this, testView);

                // Hide the discussion by clicking the toggle button again
                testView.$('.discussion-show').click();

                // Verify that the discussion is now hidden
                expect(showButton).not.toHaveClass('shown');
                expect(showButton.text().trim()).toEqual('Show Discussion');
                expect(testView.$('.inline-discussion:visible')).toHaveClass('is-hidden');
            });
        });

        describe('new post form', function() {
            it('should not be visible when the discussion is first shown', function() {
                var testView = createTestView(this);
                showDiscussion(this, testView);
                expect(testView.$('.new-post-article')).toHaveClass('is-hidden');
            });

            it('should be shown when the "Add a Post" button is clicked', function() {
                var testView = createTestView(this);
                showDiscussion(this, testView);
                testView.$('.new-post-btn').click();
                expect(testView.$('.new-post-article')).not.toHaveClass('is-hidden');
            });

            it('should be hidden when the "Cancel" button is clicked', function() {
                var testView = createTestView(this);
                showDiscussion(this, testView);
                testView.$('.new-post-btn').click();
                testView.$('.forum-new-post-form .cancel').click();
                expect(testView.$('.new-post-article')).toHaveClass('is-hidden');
            });

            it('should be hidden when the "close" button is clicked', function() {
                var testView = createTestView(this);
                showDiscussion(this, testView);
                testView.$('.new-post-btn').click();
                testView.$('.forum-new-post-form .add-post-cancel').click();
                expect(testView.$('.new-post-article')).toHaveClass('is-hidden');
            });
        });

        describe('thread listing', function() {
            it('builds a view that lists the threads', function() {
                var testView = createTestView(this);
                showDiscussion(this, testView);
                expect(testView.$('.forum-nav-thread-title').text()).toBe(TEST_THREAD_TITLE);
            });
        });

        describe('thread post drill down', function() {
            it('can drill down to a thread', function() {
                var testView = createTestView(this);
                showDiscussion(this, testView);
                testView.$('.forum-nav-thread-link').click();

                // Verify that the list of threads is hidden
                expect(testView.$('.inline-threads')).toHaveClass('is-hidden');

                // Verify that the individual thread is shown
                expect(testView.$('.group-visibility-label').text().trim()).toBe('This post is visible to everyone.');
            });

            it('can go back to the list of threads', function() {
                var testView = createTestView(this);
                showDiscussion(this, testView);
                testView.$('.forum-nav-thread-link').click();
                testView.$('.all-posts-btn').click();

                // Verify that the list of threads is shown
                expect(testView.$('.inline-threads')).not.toHaveClass('is-hidden');

                // Verify that the individual thread is no longer shown
                expect(testView.$('.group-visibility-label').length).toBe(0);
            });
        });
    });
}());
