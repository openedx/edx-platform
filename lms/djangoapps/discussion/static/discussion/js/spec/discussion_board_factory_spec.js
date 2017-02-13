define(
    [
        'jquery',
        'backbone',
        'common/js/spec_helpers/page_helpers',
        'common/js/spec_helpers/discussion_spec_helper',
        'discussion/js/discussion_board_factory',
        'discussion/js/views/discussion_board_view'
    ],
    function($, Backbone, PageHelpers, DiscussionSpecHelper, DiscussionBoardFactory, DiscussionBoardView) {
        'use strict';

        // TODO: re-enable when this doesn't interact badly with other history tests
        describe('DiscussionBoardFactory', function() {
            var createDiscussionBoardView = function() {
                var discussionBoardView,
                    discussion = DiscussionSpecHelper.createTestDiscussion({}),
                    courseSettings = DiscussionSpecHelper.createTestCourseSettings();

                setFixtures('<div class="discussion-board"><div class="forum-search"></div></div>');
                DiscussionSpecHelper.setUnderscoreFixtures();

                discussionBoardView = new DiscussionBoardView({
                    el: $('.discussion-board'),
                    discussion: discussion,
                    courseSettings: courseSettings
                });

                return discussionBoardView;
            };

            var initializeDiscussionBoardFactory = function() {
                DiscussionBoardFactory({
                    el: $('#discussion-container'),
                    courseId: 'test_course_id',
                    course_name: 'Test Course',
                    user_info: DiscussionSpecHelper.getTestUserInfo(),
                    roles: DiscussionSpecHelper.getTestRoleInfo(),
                    sort_preference: null,
                    threads: [],
                    thread_pages: [],
                    content_info: null,
                    course_settings: {
                        is_cohorted: false,
                        allow_anonymous: false,
                        allow_anonymous_to_peers: false,
                        cohorts: [],
                        category_map: {}
                    }
                });
            };

            beforeEach(function() {
                // Install the fixtures
                setFixtures(
                    '<div id="discussion-container" class="discussion-board"></div></div>'
                );
                PageHelpers.preventBackboneChangingUrl();
                DiscussionSpecHelper.setUnderscoreFixtures();
            });

            afterEach(function() {
                Backbone.history.stop();
            });

            xit('can render itself', function() { // this failed Search: navigates to search, and TeamsTab
                var discussionView = createDiscussionBoardView();
                discussionView.render();
                initializeDiscussionBoardFactory();
                expect(discussionView.$el.text()).toContain('Search all posts');
            });
        });
    }
);
