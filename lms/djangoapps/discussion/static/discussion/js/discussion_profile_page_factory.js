(function(define) {
    'use strict';

    define(
        [
            'jquery',
            'backbone',
            'common/js/discussion/content',
            'common/js/discussion/discussion',
            'common/js/discussion/utils',
            'common/js/discussion/models/discussion_user',
            'common/js/discussion/models/discussion_course_settings',
            'discussion/js/views/discussion_user_profile_view'
        ],
        function($, Backbone, Content, Discussion, DiscussionUtil, DiscussionUser, DiscussionCourseSettings,
            DiscussionUserProfileView) {
            return function(options) {
                var threads = options.threads,
                    contentInfo = options.contentInfo,
                    userInfo = options.userInfo,
                    user = new DiscussionUser(userInfo),
                    page = options.page,
                    numPages = options.numPages,
                    sortPreference = options.sortPreference,
                    discussionUserProfileView,
                    discussion,
                    courseSettings;

                // Roles are not included in user profile page, but they are not used for anything
                DiscussionUtil.loadRoles({
                    Moderator: [],
                    Administrator: [],
                    'Community TA': []
                });

                DiscussionUtil.loadRoles(options.roles);
                window.$$course_id = options.courseId;
                window.courseName = options.course_name;
                DiscussionUtil.setUser(user);
                window.user = user;
                Content.loadContentInfos(contentInfo);

                // Create a discussion model
                discussion = new Discussion(threads, {pages: numPages, sort: sortPreference});
                courseSettings = new DiscussionCourseSettings(options.courseSettings);

                discussionUserProfileView = new DiscussionUserProfileView({
                    el: $('.discussion-user-threads'),
                    discussion: discussion,
                    page: page,
                    numPages: numPages,
                    courseSettings: courseSettings
                });
                discussionUserProfileView.render();
            };
        });
}).call(this, define || RequireJS.define);
