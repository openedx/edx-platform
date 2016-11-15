(function(define) {
    'use strict';

    define(
        [
            'jquery',
            'common/js/discussion/utils',
            'common/js/discussion/models/discussion_user',
            'discussion/js/views/discussion_user_profile_view'
        ],
        function($, DiscussionUtil, DiscussionUser, DiscussionUserProfileView) {
            return function(options) {
                var $element = options.$el,
                    threads = options.threads,
                    userInfo = options.userInfo,
                    page = options.page,
                    numPages = options.numPages;
                // Roles are not included in user profile page, but they are not used for anything
                DiscussionUtil.loadRoles({
                    Moderator: [],
                    Administrator: [],
                    'Community TA': []
                });

                // TODO: remove global variable usage
                window.$$course_id = options.courseId;
                window.user = new DiscussionUser(userInfo);

                new DiscussionUserProfileView({  // eslint-disable-line no-new
                    el: $element,
                    collection: threads,
                    page: page,
                    numPages: numPages
                });
            };
        });
}).call(this, define || RequireJS.define);
