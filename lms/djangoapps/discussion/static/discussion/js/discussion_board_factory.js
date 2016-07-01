;(function(define) {
    'use strict';

    define(['jquery', 'backbone'],
        function($, Backbone) {
            return function(options) {
                var element = options.el,
                    userInfo = element.data('user-info'),
                    sortPreference = element.data('sort-preference'),
                    threads = element.data('threads'),
                    threadPages = element.data('thread-pages'),
                    contentInfo = element.data('content-info'),
                    user = new window.DiscussionUser(userInfo),
                    discussion,
                    courseSettings;
                // TODO: Perhaps eliminate usage of global variables when possible
                window.DiscussionUtil.loadRolesFromContainer();
                window.$$course_id = options.courseId;
                window.courseName = element.data('course-name');
                window.DiscussionUtil.setUser(user);
                window.user = user;
                window.Content.loadContentInfos(contentInfo);
                discussion = new window.Discussion(threads, {pages: threadPages, sort: sortPreference});
                courseSettings = new window.DiscussionCourseSettings(element.data('course-settings'));
                // jshint nonew:false
                new window.DiscussionRouter({
                    discussion: discussion,
                    course_settings: courseSettings
                });
                Backbone.history.start({
                    pushState: true,
                    root: '/courses/' + options.courseId + '/discussion/forum/'
                });
            };
        });
}).call(this, define || RequireJS.define);
