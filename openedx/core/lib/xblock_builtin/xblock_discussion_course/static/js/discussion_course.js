/* globals window, $$course_id, DiscussionUtil */
function DiscussionCourseBlock(runtime, element) {
    'use strict';
    var $discussionContainer = $("#discussion-container");
    DiscussionUtil.force_async = true;

    // stop history if it is already started.
    if (Backbone.History.started) {
        Backbone.history.stop();
    }
    function defineDiscussionClasses(define) {
        'use strict';
        var discussionClasses = [
            ['Content', 'common/js/discussion/content'],
            ['Discussion', 'common/js/discussion/discussion'],
            ['DiscussionModuleView', 'common/js/discussion/discussion_module_view'],
            ['DiscussionThreadView', 'common/js/discussion/views/discussion_thread_view'],
            ['DiscussionThreadListView', 'common/js/discussion/views/discussion_thread_list_view'],
            ['DiscussionThreadProfileView', 'common/js/discussion/views/discussion_thread_profile_view'],
            ['DiscussionTopicMenuView', 'common/js/discussion/views/discussion_topic_menu_view'],
            ['DiscussionUtil', 'common/js/discussion/utils'],
            ['DiscussionCourseSettings', 'common/js/discussion/models/discussion_course_settings'],
            ['DiscussionUser', 'common/js/discussion/models/discussion_user'],
            ['NewPostView', 'common/js/discussion/views/new_post_view']
        ];

        discussionClasses.forEach(function(discussionClass) {
            define(
                discussionClass[1],
                [],
                function() {
                    return window[discussionClass[0]];
                }
            );
        });
    };

    function initializeDiscussion() {

        if (typeof RequireJS === 'undefined') {
            var vendorScript = document.createElement("script");
            vendorScript.onload = function() {
                require.config({
                    baseUrl: "/static/",
                });

                var requireConfigScript = document.createElement("script");
                requireConfigScript.onload = function() {
                    defineDiscussionClasses(define);
                    initializeDiscussionBoardFactory(require)
                };
                requireConfigScript.src = "/static/lms/js/require-config.js";
                document.body.appendChild(requireConfigScript);
            };
            vendorScript.src = "/static/common/js/vendor/require.js";
            document.body.appendChild(vendorScript);

        } else {
            defineDiscussionClasses(RequireJS.define);
            initializeDiscussionBoardFactory(RequireJS.require);
        }
    };

    function initializeDiscussionBoardFactory(require) {
        require(
            ['discussion/js/discussion_board_factory'],
            function (DiscussionBoardFactory) {
                DiscussionBoardFactory({
                    courseId: $discussionContainer.data('courseId'),
                    course_name: $discussionContainer.data('course-name'),
                    $el: $discussionContainer,
                    user_info: $discussionContainer.data('userInfo'),
                    roles: $discussionContainer.data('roles'),
                    sort_preference: $discussionContainer.data('sortPreference'),
                    threads: $discussionContainer.data('threads'),
                    thread_pages: $discussionContainer.data('threadPages'),
                    content_info: $discussionContainer.data('contentInfo'),
                    course_settings: $discussionContainer.data('courseSettings')
                });
            }
        )
    };

    initializeDiscussion();
}
