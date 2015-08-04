define([
    'underscore', 'common/js/spec_helpers/ajax_helpers', 'teams/js/views/team_discussion',
    'teams/js/spec_helpers/team_discussion_helpers',
    'xmodule_js/common_static/coffee/spec/discussion/discussion_spec_helper'
], function (_, AjaxHelpers, TeamDiscussionView, TeamDiscussionSpecHelper, DiscussionSpecHelper) {
    'use strict';
    describe('TeamDiscussionView', function() {
        var discussionView, createDiscussionView;

        beforeEach(function() {
            setFixtures('<div class="discussion-module""></div>');
            $('.discussion-module').data('course-id', TeamDiscussionSpecHelper.testCourseID);
            $('.discussion-module').data('discussion-id', TeamDiscussionSpecHelper.testTeamDiscussionID);
            $('.discussion-module').data('user-create-comment', true);
            $('.discussion-module').data('user-create-subcomment', true);
            DiscussionSpecHelper.setUnderscoreFixtures();
        });

        createDiscussionView = function(requests) {
            discussionView = new TeamDiscussionView({
                el: '.discussion-module'
            });
            discussionView.render();
            AjaxHelpers.expectRequest(requests, 'GET', '/courses/course/1/discussion/forum/12345/inline?page=1&ajax=1');
            AjaxHelpers.respondWithJson(requests, TeamDiscussionSpecHelper.createMockDiscussionResponse());
            return discussionView;
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
            view.$('.new-post-button').click();
            view.$('.js-post-post-title').val(testTitle);
            view.$('.js-post-body textarea').val(testBody);
            view.$('.submit').click();
            AjaxHelpers.expectRequest(
                requests, 'POST', '/courses/course/1/discussion/12345/threads/create?ajax=1',
                'thread_type=discussion&title=&body=New+post+body&anonymous=false&anonymous_to_peers=false&auto_subscribe=true'
            );
            AjaxHelpers.respondWithJson(requests, {
                content: TeamDiscussionSpecHelper.createMockPostResponse({
                    id: "999", title: testTitle, body: testBody
                }),
                annotated_content_info: TeamDiscussionSpecHelper.createAnnotatedContentInfo()
            });

            // Expect the first thread to be the new post
            expect(view.$('.discussion-thread').length).toEqual(4);
            newThreadElement = view.$('.discussion-thread').first();
            expect(newThreadElement.find('.post-header-content h1').text().trim()).toEqual(testTitle);
            expect(newThreadElement.find('.post-body').text().trim()).toEqual(testBody);
        });

        it('can post a reply', function() {
            var requests = AjaxHelpers.requests(this),
                view = createDiscussionView(requests),
                replyForm,
                testReply = "Test reply";

            // Expand the replies
            view.$('.forum-thread-expand').first().click();
            AjaxHelpers.expectRequest(
                requests, 'GET', '/courses/course/1/discussion/forum/12345/threads/1?ajax=1&resp_skip=0&resp_limit=25'
            );
            AjaxHelpers.respondWithJson(requests, {
                content: TeamDiscussionSpecHelper.createMockThreadResponse({
                    body: testReply
                }),
                annotated_content_info: TeamDiscussionSpecHelper.createAnnotatedContentInfo()
            });
            replyForm = view.$('.discussion-reply-new').first();

            // Post a new reply
            replyForm.find('.reply-body textarea').val(testReply);
            replyForm.find('.discussion-submit-post').click();
            AjaxHelpers.expectRequest(
                requests, 'POST', '/courses/course/1/discussion/threads/1/reply?ajax=1',
                'body=Test+reply'
            );
            AjaxHelpers.respondWithJson(requests, {
                content: TeamDiscussionSpecHelper.createMockThreadResponse({
                    body: testReply,
                    comments_count: 1
                }),
                "annotated_content_info": TeamDiscussionSpecHelper.createAnnotatedContentInfo()
            });
            expect(view.$('.discussion-response .response-body').text().trim()).toBe(testReply);
        });

        it('cannot move a thread to a different topic', function() {
            var requests = AjaxHelpers.requests(this),
                view = createDiscussionView(requests),
                postTopicButton, updatedThreadElement,
                updatedTitle = 'Updated title',
                updatedBody = 'Updated body';
            view.$('.forum-thread-expand').first().click();
            view.$('.action-more .icon').first().click();
            view.$('.action-edit').first().click();
            postTopicButton = view.$('.post-topic');
            expect(postTopicButton.length).toBe(0);
            view.$('.js-post-post-title').val(updatedTitle);
            view.$('.js-post-body textarea').val(updatedBody);
            view.$('.submit').click();
            AjaxHelpers.expectRequest(
                requests, 'POST', '/courses/course/1/discussion/12345/threads/create?ajax=1',
                'thread_type=discussion&title=&body=Updated+body&anonymous=false&anonymous_to_peers=false&auto_subscribe=true'
            );
            AjaxHelpers.respondWithJson(requests, {
                content: TeamDiscussionSpecHelper.createMockPostResponse({
                    id: "999", title: updatedTitle, body: updatedBody
                }),
                annotated_content_info: TeamDiscussionSpecHelper.createAnnotatedContentInfo()
            });

            // Expect the thread to have been updated
            updatedThreadElement = view.$('.discussion-thread').first();
            expect(updatedThreadElement.find('.post-header-content h1').text().trim()).toEqual(updatedTitle);
            expect(updatedThreadElement.find('.post-body').text().trim()).toEqual(updatedBody);
        });
    });
});
