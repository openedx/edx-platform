/* global Content, Discussion, DiscussionCourseSettings, DiscussionUtil, DiscussionUser */
(function() {
    'use strict';
    this.DiscussionSpecHelper = (function() {
        function DiscussionSpecHelper() {
        }

        DiscussionSpecHelper.setUpGlobals = function(opts) {
            var options = opts || {};
            DiscussionUtil.loadRoles(options.roles || DiscussionSpecHelper.getTestRoleInfo());
            window.$$course_id = options.courseName || 'edX/999/test';
            window.user = new DiscussionUser(options.userInfo || DiscussionSpecHelper.getTestUserInfo());
            DiscussionUtil.setUser(window.user);
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
                Moderator: [],
                Administrator: [],
                'Community TA': []
            };
        };

        DiscussionSpecHelper.makeTA = function() {
            return DiscussionUtil.roleIds['Community TA'].push(parseInt(DiscussionUtil.getUser().id, 10));
        };

        DiscussionSpecHelper.makeModerator = function() {
            return DiscussionUtil.roleIds.Moderator.push(parseInt(DiscussionUtil.getUser().id, 10));
        };

        DiscussionSpecHelper.makeAjaxSpy = function(fakeAjax) {
            return spyOn($, 'ajax').and.callFake(function(params) {
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

        DiscussionSpecHelper.createTestCourseSettings = function(options) {
            var context = _.extend(
                {
                    category_map: {
                        children: [['Test Topic', 'entry'], ['Other Topic', 'entry']],
                        entries: {
                            'Test Topic': {
                                is_cohorted: true,
                                id: 'test_topic'
                            },
                            'Other Topic': {
                                is_cohorted: true,
                                id: 'other_topic'
                            }
                        }
                    },
                    is_cohorted: true,
                    allow_anonymous: false,
                    allow_anonymous_to_peers: false
                },
                options || {}
            );
            return new DiscussionCourseSettings(context);
        };

        DiscussionSpecHelper.createTestDiscussion = function(options) {
            var sortPreference = options.sort_preference,
                threads = options.threads || [],
                threadPages = options.thread_pages || 1,
                contentInfo = options.content_info;
            DiscussionSpecHelper.setUpGlobals(options);
            if (contentInfo) {
                Content.loadContentInfos(contentInfo);
            }
            return new Discussion(threads, {pages: threadPages, sort: sortPreference});
        };

        DiscussionSpecHelper.setUnderscoreFixtures = function() {
            var templateFixture, templateName, templateNames, templateNamesNoTrailingTemplate, i, j, len;
            templateNames = [
                'thread', 'thread-show', 'thread-edit', 'thread-response', 'thread-response-show',
                'thread-response-edit', 'response-comment-show', 'response-comment-edit', 'thread-list-item',
                'search-alert', 'new-post', 'thread-type', 'new-post-menu-entry', 'new-post-alert',
                'new-post-menu-category', 'topic', 'post-user-display', 'inline-discussion', 'pagination',
                'profile-thread', 'customwmd-prompt', 'nav-loading'
            ];
            templateNamesNoTrailingTemplate = [
                'forum-action-endorse', 'forum-action-answer', 'forum-action-follow', 'forum-action-vote',
                'forum-action-report', 'forum-action-pin', 'forum-action-close', 'forum-action-edit',
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

            appendSetFixtures(
                '<script type="text/template" id="thread-list-template">' +
                '    <div class="forum-nav-header">' +
                '        <button type="button" class="forum-nav-browse" id="forum-nav-browse" aria-haspopup="true">' +
                '            <span class="icon fa fa-bars" aria-hidden="true"></span>' +
                '            <span class="sr">Discussion topics; currently listing: </span>' +
                '            <span class="forum-nav-browse-current">All Discussions</span>' +
                '        </button>' +
                '        <form class="forum-nav-search">' +
                '            <label>' +
                '                <span class="sr">Search all posts</span>' +
                '                <input' +
                '                    class="forum-nav-search-input"' +
                '                    id="forum-nav-search"' +
                '                    type="text"' +
                '                    placeholder="Search all posts"' +
                '                >' +
                '                <span class="icon fa fa-search" aria-hidden="true"></span>' +
                '            </label>' +
                '        </form>' +
                '    </div>' +
                '    <div class="forum-nav-browse-menu-wrapper" style="display: none">' +
                '        <form class="forum-nav-browse-filter">' +
                '            <label>' +
                '                <span class="sr">Filter Topics</span>' +
                '                <input' +
                '                    type="text"' +
                '                    class="forum-nav-browse-filter-input"' +
                '                    placeholder="filter topics"' +
                '                >' +
                '            </label>' +
                '        </form>' +
                '        <ul class="forum-nav-browse-menu">' +
                '            <li class="forum-nav-browse-menu-item forum-nav-browse-menu-all">' +
                '                <a href="#" class="forum-nav-browse-title">All Discussions</a>' +
                '            </li>' +
                '            <li class="forum-nav-browse-menu-item forum-nav-browse-menu-following">' +
                '                <a href="#" class="forum-nav-browse-title">' +
                '                    <span class="icon fa fa-star" aria-hidden="true"></span>' +
                '                    Posts I\'m Following' +
                '                </a>' +
                '            </li>' +
                '            <li class="forum-nav-browse-menu-item">' +
                '                <a href="#" class="forum-nav-browse-title">Parent</a>' +
                '                <ul class="forum-nav-browse-submenu">' +
                '                    <li class="forum-nav-browse-menu-item">' +
                '                        <a href="#" class="forum-nav-browse-title">Target</a>' +
                '                        <ul class="forum-nav-browse-submenu">' +
                '                            <li' +
                '                                class="forum-nav-browse-menu-item"' +
                '                                data-discussion-id="child"' +
                '                                data-cohorted="false"' +
                '                            >' +
                '                                <a href="#" class="forum-nav-browse-title">Child</a>' +
                '                            </li>' +
                '                        </ul>' +
                '                    <li' +
                '                        class="forum-nav-browse-menu-item"' +
                '                        data-discussion-id="sibling"' +
                '                        data-cohorted="false"' +
                '                    >' +
                '                        <a href="#" class="forum-nav-browse-title">Sibling</a>' +
                '                    </li>' +
                '                </ul>' +
                '            </li>' +
                '            <li' +
                '                class="forum-nav-browse-menu-item"' +
                '                data-discussion-id="other"' +
                '                data-cohorted="true"' +
                '            >' +
                '                <a href="#" class="forum-nav-browse-title">Other Category</a>' +
                '            </li>' +
                '        </ul>' +
                '    </div>' +
                '    <div class="forum-nav-thread-list-wrapper" id="sort-filter-wrapper" tabindex="-1">' +
                '        <div class="forum-nav-refine-bar">' +
                '            <label class="forum-nav-filter-main">' +
                '                <select class="forum-nav-filter-main-control">' +
                '                    <option value="all">Show all</option>' +
                '                    <option value="unread">Unread</option>' +
                '                    <option value="unanswered">Unanswered</option>' +
                '                    <option value="flagged">Flagged</option>' +
                '                </select>' +
                '            </label>' +
                '            <% if (isCohorted && isPrivilegedUser) { %>' +
                '            <label class="forum-nav-filter-cohort">' +
                '                <span class="sr">Cohort:</span>' +
                '                <select class="forum-nav-filter-cohort-control">' +
                '                    <option value="">in all cohorts</option>' +
                '                    <option value="1">Cohort1</option>' +
                '                    <option value="2">Cohort2</option>' +
                '                </select>' +
                '            </label>' +
                '            <% } %>' +
                '            <label class="forum-nav-sort">' +
                '                <select class="forum-nav-sort-control">' +
                '                    <option value="activity">by recent activity</option>' +
                '                    <option value="comments">by most activity</option>' +
                '                    <option value="votes">by most votes</option>' +
                '                </select>' +
                '            </label>' +
                '        </div>' +
                '    </div>' +
                '    <div class="search-alerts"></div>' +
                '    <ul class="forum-nav-thread-list"></ul>' +
                '</script>'
            );

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
    }());
}).call(this);
