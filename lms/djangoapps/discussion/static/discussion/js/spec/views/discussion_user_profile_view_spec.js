/* globals Discussion, DiscussionCourseSettings */
define([
    'underscore',
    'jquery',
    'URI',
    'common/js/discussion/utils',
    'common/js/discussion/views/discussion_thread_profile_view',
    'common/js/discussion/discussion',
    'common/js/spec_helpers/discussion_spec_helper',
    'discussion/js/views/discussion_user_profile_view'
],
function(_, $, URI, DiscussionUtil, DiscussionThreadProfileView, Discussion,
DiscussionSpecHelper, DiscussionUserProfileView) {
    'use strict';
    describe('DiscussionUserProfileView', function() {
        var createDiscussionUserProfileView = function() {
            var discussion = DiscussionSpecHelper.createTestDiscussion({}),
                courseSettings = DiscussionSpecHelper.createTestCourseSettings();

            setFixtures('<div class="discussion-user-profile-board"></div>');
            DiscussionSpecHelper.setUnderscoreFixtures();

            return new DiscussionUserProfileView({
                el: $('.discussion-user-profile-board'),
                discussion: discussion,
                courseSettings: courseSettings,
                sortPreference: null
            });
        };

        describe('thread list in user profile page', function() {
            it('should render', function() {
                var discussionUserProfileView = createDiscussionUserProfileView().render(),
                    threadListView = discussionUserProfileView.discussionThreadListView.render();
                expect(threadListView.$('.forum-nav-thread-list').length).toBe(1);
            });

            it('should ensure discussion thread list view mode is all', function() {
                var discussionUserProfileView = createDiscussionUserProfileView().render(),
                    threadListView = discussionUserProfileView.discussionThreadListView.render();
                expect(threadListView.mode).toBe('user');
            });

            it('should not show the thread list unread unanswered filter', function() {
                var discussionUserProfileView = createDiscussionUserProfileView().render(),
                    threadListView = discussionUserProfileView.discussionThreadListView.render();
                expect(threadListView.$('.forum-nav-filter-main')).toHaveClass('is-hidden');
            });
        });
    });
});
