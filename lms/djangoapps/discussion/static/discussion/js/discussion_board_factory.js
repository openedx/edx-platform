(function(define) {
    'use strict';

    define(
        [
            'jquery',
            'backbone',
            'common/js/discussion/content',
            'common/js/discussion/discussion',
            'common/js/discussion/utils',
            'common/js/discussion/models/discussion_course_settings',
            'common/js/discussion/models/discussion_user',
            'common/js/discussion/views/new_post_view',
            'discussion/js/discussion_router',
            'discussion/js/views/discussion_board_view'
        ],
        function($, Backbone, Content, Discussion, DiscussionUtil, DiscussionCourseSettings, DiscussionUser,
                 NewPostView, DiscussionRouter, DiscussionBoardView) {
            return function(options) {
                var userInfo = options.userInfo,
                    sortPreference = options.sortPreference,
                    threads = options.threads,
                    threadPages = options.threadPages,
                    isCommentableDivided = options.isCommentableDivided,
                    contentInfo = options.contentInfo,
                    user = new DiscussionUser(userInfo),
                    discussion,
                    courseSettings,
                    newPostView,
                    discussionBoardView,
                    router,
                    routerEvents;

                // TODO: eliminate usage of global variables when possible
                if (options.roles === undefined) {
                    options.roles = {};
                }
                DiscussionUtil.loadRoles(options.roles);
                window.$$course_id = options.courseId;
                window.courseName = options.courseName;
                DiscussionUtil.setUser(user);
                window.user = user;
                Content.loadContentInfos(contentInfo);

                // Create a discussion model
                discussion = new Discussion(threads, {pages: threadPages, sort: sortPreference,
                    is_commentable_divided: isCommentableDivided});
                courseSettings = new DiscussionCourseSettings(options.courseSettings);

                // Create the discussion board view
                discussionBoardView = new DiscussionBoardView({
                    el: $('.discussion-board'),
                    discussion: discussion,
                    courseSettings: courseSettings
                });
                discussionBoardView.render();

                // Create the new post view
                newPostView = new NewPostView({
                    el: $('.new-post-article'),
                    collection: discussion,
                    course_settings: courseSettings,
                    discussionBoardView: discussionBoardView,
                    mode: 'tab',
                    startHeader: 2,
                    topicId: options.defaultTopicId
                });
                newPostView.render();

                // Set up a router to manage the page's history
                router = new DiscussionRouter({
                    rootUrl: options.rootUrl,
                    discussion: discussion,
                    courseSettings: courseSettings,
                    discussionBoardView: discussionBoardView,
                    newPostView: newPostView
                });
                router.start();
                routerEvents = {
                    // Add new breadcrumbs and clear search box when the user selects topics
                    'topic:selected': function(topic) {
                        router.discussionBoardView.breadcrumbs.model.set('contents', topic);
                    },
                    // Clear search box when a thread is selected
                    'thread:selected': function() {
                        router.discussionBoardView.searchView.clearSearch();
                    }
                };
                Object.keys(routerEvents).forEach(function(key) {
                    router.discussionBoardView.on(key, routerEvents[key]);
                });
            };
        });
}).call(this, define || RequireJS.define);
