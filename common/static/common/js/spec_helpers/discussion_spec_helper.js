/* global DiscussionCourseSettings, DiscussionUtil, DiscussionUser */
(function() {
    'use strict';
    this.DiscussionSpecHelper = (function() {
        function DiscussionSpecHelper() {
        }

        DiscussionSpecHelper.setUpGlobals = function() {
            DiscussionUtil.loadRoles({
                'Moderator': [],
                'Administrator': [],
                'Community TA': []
            });
            window.$$course_id = 'edX/999/test';
            window.user = new DiscussionUser({
                username: 'test_user',
                id: '567',
                upvoted_ids: []
            });
            return DiscussionUtil.setUser(window.user);
        };

        DiscussionSpecHelper.makeTA = function() {
            return DiscussionUtil.roleIds['Community TA'].push(parseInt(DiscussionUtil.getUser().id));
        };

        DiscussionSpecHelper.makeModerator = function() {
            return DiscussionUtil.roleIds.Moderator.push(parseInt(DiscussionUtil.getUser().id));
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

        DiscussionSpecHelper.makeCourseSettings = function(is_cohorted) {
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
            var templateFixture, templateName, templateNames, templateNamesNoTrailingTemplate, _i, _j, _len, _len1;
            templateNames = [
                'thread', 'thread-show', 'thread-edit', 'thread-response', 'thread-response-show',
                'thread-response-edit', 'response-comment-show', 'response-comment-edit', 'thread-list-item',
                'discussion-home', 'search-alert', 'new-post', 'thread-type', 'new-post-menu-entry',
                'new-post-menu-category', 'topic', 'post-user-display', 'inline-discussion', 'pagination',
                'user-profile', 'profile-thread', 'customwmd-prompt', 'nav-loading'
            ];
            templateNamesNoTrailingTemplate = [
                'forum-action-endorse', 'forum-action-answer', 'forum-action-follow', 'forum-action-vote',
                'forum-action-report', 'forum-action-pin', 'forum-action-close', 'forum-action-edit',
                'forum-action-delete', 'forum-actions', 'alert-popup', 'nav-load-more-link'
            ];
            for (_i = 0, _len = templateNames.length; _i < _len; _i++) {
                templateName = templateNames[_i];
                templateFixture = readFixtures('common/templates/discussion/' + templateName + '.underscore');
                appendSetFixtures($('<script>', {
                    id: templateName + '-template',
                    type: 'text/template'
                }).text(templateFixture));
            }
            for (_j = 0, _len1 = templateNamesNoTrailingTemplate.length; _j < _len1; _j++) {
                templateName = templateNamesNoTrailingTemplate[_j];
                templateFixture = readFixtures('common/templates/discussion/' + templateName + '.underscore');
                appendSetFixtures($('<script>', {
                    id: templateName,
                    type: 'text/template'
                }).text(templateFixture));
            }
            return appendSetFixtures(
                '<div id="fixture-element"></div>\n' +
                '<div id="discussion-container"' +
                '   data-course-name="Fake Course"' +
                '   data-user-create-comment="true"' +
                '   data-user-create-subcomment="true"' +
                '   data-read-only="false"' +
                '></div>'
            );
        };

        return DiscussionSpecHelper;
    })();
}).call(this);
