(function(define) {
    'use strict';

    define(['jquery', 'discussion/js/views/discussion_user_profile_view'],
        function($, DiscussionUserProfileView) {
            return function(options) {
                var $element = options.$el,
                    threads = options.threads,
                    userInfo = options.userInfo,
                    page = options.page,
                    numPages = options.numPages;
                // Roles are not included in user profile page, but they are not used for anything
                window.DiscussionUtil.loadRoles({
                    Moderator: [],
                    Administrator: [],
                    'Community TA': []
                });
                window.$$course_id = options.courseId;
                window.user = new window.DiscussionUser(userInfo);
                new DiscussionUserProfileView({  // eslint-disable-line no-new
                    el: $element,
                    collection: threads,
                    page: page,
                    numPages: numPages
                });
            };
        });
}).call(this, define || RequireJS.define);
