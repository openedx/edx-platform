define([
    'underscore', 'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers', 'teams/js/views/team_discussion',
    'teams/js/spec_helpers/team_spec_helpers',
    'xmodule_js/common_static/common/js/spec_helpers/discussion_spec_helper'
], function(_, AjaxHelpers, TeamDiscussionView, TeamSpecHelpers, DiscussionSpecHelper) {
    'use strict';
    xdescribe('TeamDiscussionView', function() {
        var discussionView, createDiscussionView, createPost, expandReplies, postReply;

        beforeEach(function() {
            setFixtures('<div class="discussion-module""></div>');
            $('.discussion-module').data('course-id', TeamSpecHelpers.testCourseID);
            $('.discussion-module').data('discussion-id', TeamSpecHelpers.testTeamDiscussionID);
            $('.discussion-module').data('user-create-comment', true);
            $('.discussion-module').data('user-create-subcomment', true);
            DiscussionSpecHelper.setUnderscoreFixtures();
        });

        createDiscussionView = function(requests, threads) {
            discussionView = new TeamDiscussionView({
                el: '.discussion-module'
            });
            discussionView.render();
            AjaxHelpers.expectRequest(
                requests, 'GET',
                interpolate(
                    '/courses/%(courseID)s/discussion/forum/%(discussionID)s/inline?page=1&ajax=1',
                    {
                        courseID: TeamSpecHelpers.testCourseID,
                        discussionID: TeamSpecHelpers.testTeamDiscussionID
                    },
                    true

                )
            );
            AjaxHelpers.respondWithJson(requests, TeamSpecHelpers.createMockDiscussionResponse(threads));
            return discussionView;
        };

        createPost = function(requests, view, title, body, threadID) {
            title = title || 'Test title';
            body = body || 'Test body';
            threadID = threadID || '999';
            view.$('.new-post-button').click();
            view.$('.js-post-title').val(title);
            view.$('.js-post-body textarea').val(body);
            view.$('.submit').click();
            AjaxHelpers.expectRequest(
                requests, 'POST',
                interpolate(
                    '/courses/%(courseID)s/discussion/%(discussionID)s/threads/create?ajax=1',
                    {
                        courseID: TeamSpecHelpers.testCourseID,
                        discussionID: TeamSpecHelpers.testTeamDiscussionID
                    },
                    true
                ),
                interpolate(
                    'thread_type=discussion&title=%(title)s&body=%(body)s&anonymous=false&anonymous_to_peers=false&auto_subscribe=true',
                    {
                        title: title.replace(/ /g, '+'),
                        body: body.replace(/ /g, '+')
                    },
                    true
                )
            );
            AjaxHelpers.respondWithJson(requests, {
                content: TeamSpecHelpers.createMockPostResponse({
                    id: threadID,
                    title: title,
                    body: body
                }),
                annotated_content_info: TeamSpecHelpers.createAnnotatedContentInfo()
            });
        };

        expandReplies = function(requests, view, threadID) {
            view.$('.forum-thread-expand').first().click();
            AjaxHelpers.expectRequest(
                requests, 'GET',
                interpolate(
                    '/courses/%(courseID)s/discussion/forum/%(discussionID)s/threads/%(threadID)s?ajax=1&resp_skip=0&resp_limit=25',
                    {
                        courseID: TeamSpecHelpers.testCourseID,
                        discussionID: TeamSpecHelpers.testTeamDiscussionID,
                        threadID: threadID || '999'
                    },
                    true
                )
            );
            AjaxHelpers.respondWithJson(requests, {
                content: TeamSpecHelpers.createMockThreadResponse(),
                annotated_content_info: TeamSpecHelpers.createAnnotatedContentInfo()
            });
        };

        postReply = function(requests, view, reply, threadID) {
            var replyForm = view.$('.discussion-reply-new').first();
            replyForm.find('.reply-body textarea').val(reply);
            replyForm.find('.discussion-submit-post').click();
            AjaxHelpers.expectRequest(
                requests, 'POST',
                interpolate(
                    '/courses/%(courseID)s/discussion/threads/%(threadID)s/reply?ajax=1',
                    {
                        courseID: TeamSpecHelpers.testCourseID,
                        threadID: threadID || '999'
                    },
                    true
                ),
                'body=' + reply.replace(/ /g, '+')
            );
            AjaxHelpers.respondWithJson(requests, {
                content: TeamSpecHelpers.createMockThreadResponse({
                    body: reply,
                    comments_count: 1
                }),
                'annotated_content_info': TeamSpecHelpers.createAnnotatedContentInfo()
            });
        };

        it('can render itself', function() {
            var requests = AjaxHelpers.requests(this),
                view = createDiscussionView(requests);
            expect(view.$('.discussion-thread').length).toEqual(3);
        });

        it('can create a new post', function() {
            var requests = AjaxHelpers.requests(this),
                view = createDiscussionView(requests),
                testTitle = 'New Post',
                testBody = 'New post body',
                newThreadElement;
            createPost(requests, view, testTitle, testBody);

            // Expect the first thread to be the new post
            expect(view.$('.discussion-thread').length).toEqual(4);
            newThreadElement = view.$('.discussion-thread').first();
            expect(newThreadElement.find('.post-header-content h1').text().trim()).toEqual(testTitle);
            expect(newThreadElement.find('.post-body').text().trim()).toEqual(testBody);
        });

        it('can post a reply', function() {
            var requests = AjaxHelpers.requests(this),
                view = createDiscussionView(requests),
                testReply = 'Test reply',
                testThreadID = '1';
            expandReplies(requests, view, testThreadID);
            postReply(requests, view, testReply, testThreadID);
            expect(view.$('.discussion-response .response-body').text().trim()).toBe(testReply);
        });

        it('can post a reply to a new post', function() {
            var requests = AjaxHelpers.requests(this),
                view = createDiscussionView(requests, []),
                testReply = 'Test reply';
            createPost(requests, view);
            expandReplies(requests, view);
            postReply(requests, view, testReply);
            expect(view.$('.discussion-response .response-body').text().trim()).toBe(testReply);
        });

        it('cannot move an existing thread to a different topic', function() {
            var requests = AjaxHelpers.requests(this),
                view = createDiscussionView(requests),
                postTopicButton, updatedThreadElement,
                updatedTitle = 'Updated title',
                updatedBody = 'Updated body',
                testThreadID = '1';
            expandReplies(requests, view, testThreadID);
            view.$('.action-more .icon').first().click();
            view.$('.action-edit').first().click();
            postTopicButton = view.$('.post-topic');
            expect(postTopicButton.length).toBe(0);
            view.$('.js-post-post-title').val(updatedTitle);
            view.$('.js-post-body textarea').val(updatedBody);
            view.$('.submit').click();
            AjaxHelpers.expectRequest(
                requests, 'POST',
                interpolate(
                    '/courses/%(courseID)s/discussion/%(discussionID)s/threads/create?ajax=1',
                    {
                        courseID: TeamSpecHelpers.testCourseID,
                        discussionID: TeamSpecHelpers.testTeamDiscussionID
                    },
                    true
                ),
                'thread_type=discussion&title=&body=Updated+body&anonymous=false&anonymous_to_peers=false&auto_subscribe=true'
            );
            AjaxHelpers.respondWithJson(requests, {
                content: TeamSpecHelpers.createMockPostResponse({
                    id: '999', title: updatedTitle, body: updatedBody
                }),
                annotated_content_info: TeamSpecHelpers.createAnnotatedContentInfo()
            });

            // Expect the thread to have been updated
            updatedThreadElement = view.$('.discussion-thread').first();
            expect(updatedThreadElement.find('.post-header-content h1').text().trim()).toEqual(updatedTitle);
            expect(updatedThreadElement.find('.post-body').text().trim()).toEqual(updatedBody);
        });

        it('cannot move a new thread to a different topic', function() {
            var requests = AjaxHelpers.requests(this),
                view = createDiscussionView(requests),
                postTopicButton;
            createPost(requests, view);
            expandReplies(requests, view);
            view.$('.action-more .icon').first().click();
            view.$('.action-edit').first().click();
            expect(view.$('.post-topic').length).toBe(0);
        });
    });
});
