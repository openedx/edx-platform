;(function(define) {
    'use strict';

    define(['jquery', 'DiscussionUserProfileView'],
        function($, DiscussionUserProfileView) {
            return function(options) {
                var element = options.el,
                    threads = element.data('threads'),
                    userInfo = element.data('user-info'),
                    page = element.data('page'),
                    numPages = element.data('num-pages');
                // Roles are not included in user profile page, but they are not used for anything
                window.DiscussionUtil.loadRoles({
                    'Moderator': [],
                    'Administrator': [],
                    'Community TA': []
                });
                window.$$course_id = element.data('course-id');
                window.user = new window.DiscussionUser(userInfo);
                // jshint nonew:false
                new DiscussionUserProfileView({
                    el: element,
                    collection: threads,
                    page: page,
                    numPages: numPages
                });
            };
        });
}).call(this, define || RequireJS.define);
