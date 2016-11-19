/* globals
 _, Discussion, DiscussionCourseSettings, DiscussionViewSpecHelper, DiscussionSpecHelper,
 DiscussionInlineView, DiscussionUtil, Thread
 */
(function() {
    'use strict';
    describe('DiscussionInlineView', function() {
        var createTestView, setNextAjaxResult;

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
            this.courseSettings = DiscussionSpecHelper.createTestCourseSettings({

            });
            this.threadData = DiscussionViewSpecHelper.makeThreadWithProps({
                commentable_id: 'test-topic',
                title: 'Test thread title'
            });
            this.ajaxSpy = spyOn($, 'ajax');
            spyOn(DiscussionUtil, 'makeWmdEditor');
        });

        createTestView = function() {
            var testView = new DiscussionInlineView({
                el: $('.discussion-module')
            });
            testView.render();
            return testView;
        };

        setNextAjaxResult = function(test, result) {
            test.ajaxSpy.and.callFake(function(params) {
                var deferred = $.Deferred();
                deferred.resolve();
                params.success(result);
                return deferred;
            });
        };

        describe('open/close behavior', function() {

        });

        describe('new post form', function() {

        });

        describe('thread listing', function() {
            it('builds a view that has the right number of threads', function() {

            });

            it('calls DiscussionThreadListView internally', function() {

            });
        });

        describe('thread post drill down', function() {
            it('can drill down to a thread', function() {
                var testView = createTestView();
                setNextAjaxResult(this, {
                    user_info: DiscussionSpecHelper.getTestUserInfo(),
                    roles: DiscussionSpecHelper.getTestRoleInfo(),
                    course_settings: this.courseSettings.attributes,
                    discussion_data: this.threadData,
                    page: 1,
                    num_pages: 1
                });
                testView.$('.discussion-show').click();
                expect(testView).toBeTruthy();
            });

            it('can go back to the list of threads', function() {
                var testView = createTestView();
                expect(testView).toBeTruthy();
            });
        });
    });
}());
