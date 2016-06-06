define(
    [
        'jquery',
        'backbone',
        'common/js/spec_helpers/page_helpers',
        'common/js/spec_helpers/discussion_spec_helper',
        'discussion/js/discussion_board_factory'
    ],
    function($, Backbone, PageHelpers, DiscussionSpecHelper, DiscussionBoardFactory) {
        'use strict';

        // TODO: re-enable when this doesn't interact badly with other history tests
        xdescribe('Discussion Board Factory', function() {
            var initializeDiscussionBoardFactory = function() {
                DiscussionBoardFactory({
                    el: $('.discussion-board'),
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
                PageHelpers.preventBackboneChangingUrl();

                // Install the fixtures
                setFixtures(
                    '<div class="discussion-board">' +
                    '    <div class="forum-nav"></div>' +
                    '</div>'
                );
                DiscussionSpecHelper.setUnderscoreFixtures();
            });

            afterEach(function() {
                Backbone.history.stop();
            });

            it('can render itself', function() {
                initializeDiscussionBoardFactory();
                expect($('.discussion-board').text()).toContain('All Discussions');
            });
        });
    }
);
