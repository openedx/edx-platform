/* global DiscussionCourseSettings, DiscussionUtil, DiscussionUser */
(function() {
    'use strict';
    this.DiscussionSpecHelper = (function() {

        function DiscussionSpecHelper() {
        }

        DiscussionSpecHelper.setUpGlobals = function() {
            DiscussionUtil.loadRoles(DiscussionSpecHelper.getTestRoleInfo());
            window.$$course_id = 'edX/999/test';
            window.user = new DiscussionUser(DiscussionSpecHelper.getTestUserInfo());
            return DiscussionUtil.setUser(window.user);
        };

        DiscussionSpecHelper.getTestUserInfo = function() {
            return {
                username: 'test_user',
                id: '567',
                upvoted_ids: []
            };
        };

        DiscussionSpecHelper.getTestRoleInfo = function() {
            return {
                'Moderator': [],
                'Administrator': [],
                'Community TA': []
            };
        };

        DiscussionSpecHelper.makeTA = function() {
            return DiscussionUtil.roleIds['Community TA'].push(parseInt(DiscussionUtil.getUser().id));
        };

        DiscussionSpecHelper.makeModerator = function() {
            return DiscussionUtil.roleIds.Moderator.push(parseInt(DiscussionUtil.getUser().id));
        };

        DiscussionSpecHelper.makeAjaxSpy = function (fakeAjax) {
            return spyOn($, 'ajax').and.callFake(function (params) {
                fakeAjax(params);
                return {
                    always: function() {
                    }
                };
            });
        };

        DiscussionSpecHelper.makeEventSpy = function() {
            return jasmine.createSpyObj('event', ['preventDefault', 'target']);
        };

        DiscussionSpecHelper.makeCourseSettings = function (is_cohorted) {
            if (typeof is_cohorted === 'undefined' || is_cohorted === null) {
                is_cohorted = true;
            }
            return new DiscussionCourseSettings({
                category_map: {
                    children: ['Test Topic', 'Other Topic'],
                    entries: {
                        'Test Topic': {
                            is_cohorted: is_cohorted,
                            id: 'test_topic'
                        },
                        'Other Topic': {
                            is_cohorted: is_cohorted,
                            id: 'other_topic'
                        }
                    }
                },
                is_cohorted: is_cohorted
            });
        };

        DiscussionSpecHelper.setUnderscoreFixtures = function() {
            var templateFixture, templateName, templateNames, templateNamesNoTrailingTemplate, i, j, len;
            templateNames = [
                'thread', 'thread-show', 'thread-edit', 'thread-response', 'thread-response-show',
                'thread-response-edit', 'response-comment-show', 'response-comment-edit', 'thread-list-item',
                'discussion-home', 'search-alert', 'new-post', 'thread-type', 'new-post-menu-entry',
                'new-post-menu-category', 'topic', 'post-user-display', 'inline-discussion', 'pagination',
                'profile-thread', 'customwmd-prompt', 'nav-loading'
            ];
            templateNamesNoTrailingTemplate = [
                'forum-action-endorse', 'forum-action-answer', 'forum-action-follow', 'forum-action-vote',
                'forum-action-report',  'forum-action-pin', 'forum-action-close', 'forum-action-edit',
                'forum-action-delete', 'forum-actions', 'alert-popup', 'nav-load-more-link'
            ];
            for (i = 0, len = templateNames.length; i < len; i++) {
                templateName = templateNames[i];
                templateFixture = readFixtures('common/templates/discussion/' + templateName + '.underscore');
                appendSetFixtures($('<script>', {
                    id: templateName + '-template',
                    type: 'text/template'
                }).text(templateFixture));
            }
            for (j = 0, len = templateNamesNoTrailingTemplate.length; j < len; j++) {
                templateName = templateNamesNoTrailingTemplate[j];
                templateFixture = readFixtures('common/templates/discussion/' + templateName + '.underscore');
                appendSetFixtures($('<script>', {
                    id: templateName,
                    type: 'text/template'
                }).text(templateFixture));
            }

            // suppressing Line is too long (4272 characters!)
            /* jshint -W101 */
            appendSetFixtures(
                "<script type=\'text/template\' id=\'thread-list-template\'>\n    <div class=\'forum-nav-header\'>\n        <button type=\'button\' class=\'forum-nav-browse\' id=\'forum-nav-browse\' aria-haspopup=\'true\'>\n            <span class=\'icon fa fa-bars\' aria-hidden=\'true\'></span>\n            <span class=\'sr\'>Discussion topics; currently listing: </span>\n            <span class=\'forum-nav-browse-current\'>All Discussions</span>\n            ▾\n        </button>\n        <form class=\'forum-nav-search\'>\n            <label>\n                <span class=\'sr\'>Search all posts</span>\n                <input class=\'forum-nav-search-input\' id=\'forum-nav-search\' type=\'text\' placeholder=\'Search all posts\'>\n                <span class=\'icon fa fa-search\' aria-hidden=\'true\'></span>\n            </label>\n        </form>\n    </div>\n    <div class=\'forum-nav-browse-menu-wrapper\' style=\'display: none\'>\n        <form class=\'forum-nav-browse-filter\'>\n            <label>\n                <span class=\'sr\'>Filter Topics</span>\n                <input type=\'text\' class=\'forum-nav-browse-filter-input\' placeholder=\'filter topics\'>\n            </label>\n        </form>\n        <ul class=\'forum-nav-browse-menu\'>\n            <li class=\'forum-nav-browse-menu-item forum-nav-browse-menu-all\'>\n                <a href=\'#\' class=\'forum-nav-browse-title\'>All Discussions</a>\n            </li>\n            <li class=\'forum-nav-browse-menu-item forum-nav-browse-menu-following\'>\n                <a href=\'#\' class=\'forum-nav-browse-title\'><span class=\'icon fa fa-star\' aria-hidden=\'true\'></span>Posts I'm Following</a>\n            </li>\n            <li class=\'forum-nav-browse-menu-item\'>\n                <a href=\'#\' class=\'forum-nav-browse-title\'>Parent</a>\n                <ul class=\'forum-nav-browse-submenu\'>\n                    <li class=\'forum-nav-browse-menu-item\'>\n                        <a href=\'#\' class=\'forum-nav-browse-title\'>Target</a>\n                        <ul class=\'forum-nav-browse-submenu\'>\n                            <li\n                                class=\'forum-nav-browse-menu-item\'\n                                data-discussion-id=\'child\'\n                                data-cohorted=\'false\'\n                            >\n                                <a href=\'#\' class=\'forum-nav-browse-title\'>Child</a>\n                            </li>\n                        </ul>\n                    <li\n                        class=\'forum-nav-browse-menu-item\'\n                        data-discussion-id=\'sibling\'\n                        data-cohorted=\'false\'\n                    >\n                        <a href=\'#\' class=\'forum-nav-browse-title\'>Sibling</a>\n                    </li>\n                </ul>\n            </li>\n            <li\n                class=\'forum-nav-browse-menu-item\'\n                data-discussion-id=\'other\'\n                data-cohorted=\'true\'\n            >\n                <a href=\'#\' class=\'forum-nav-browse-title\'>Other Category</a>\n            </li>\n        </ul>\n    </div>\n    <div class=\'forum-nav-thread-list-wrapper\' id=\'sort-filter-wrapper\' tabindex=\'-1\'>\n        <div class=\'forum-nav-refine-bar\'>\n            <label class=\'forum-nav-filter-main\'>\n                <select class=\'forum-nav-filter-main-control\'>\n                    <option value=\'all\'>Show all</option>\n                    <option value=\'unread\'>Unread</option>\n                    <option value=\'unanswered\'>Unanswered</option>\n                    <option value=\'flagged\'>Flagged</option>\n                </select>\n            </label>\n            <% if (isCohorted && isPrivilegedUser) { %>\n            <label class=\'forum-nav-filter-cohort\'>\n                <span class=\'sr\'>Cohort:</span>\n                <select class=\'forum-nav-filter-cohort-control\'>\n                    <option value=\'\'>in all cohorts</option>\n                    <option value=\'1\'>Cohort1</option>\n                    <option value=\'2\'>Cohort2</option>\n                </select>\n            </label>\n            <% } %>\n            <label class=\'forum-nav-sort\'>\n                <select class=\'forum-nav-sort-control\'>\n                    <option value=\'activity\'>by recent activity</option>\n                    <option value=\'comments\'>by most activity</option>\n                    <option value=\'votes\'>by most votes</option>\n                </select>\n            </label>\n        </div>\n    </div>\n    <div class=\'search-alerts\'></div>\n    <ul class=\'forum-nav-thread-list\'></ul>\n</script>");

            appendSetFixtures(
                '<div id=\'fixture-element\'></div>\n' +
                '<div id=\'discussion-container\'' +
                '   data-course-name=\'Fake Course\'' +
                '   data-user-create-comment=\'true\'' +
                '   data-user-create-subcomment=\'true\'' +
                '   data-read-only=\'false\'' +
                '></div>'
            );
        };

        return DiscussionSpecHelper;

    })();

}).call(this);
