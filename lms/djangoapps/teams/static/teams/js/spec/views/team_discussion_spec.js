define([
    'underscore', 'common/js/spec_helpers/ajax_helpers', 'teams/js/views/team_discussion',
    'teams/js/spec_helpers/team_discussion_helpers',
    'xmodule_js/common_static/coffee/spec/discussion/discussion_spec_helper'
], function (_, AjaxHelpers, TeamDiscussionView, TeamDiscussionSpecHelper, DiscussionSpecHelper) {
    'use strict';
    describe('TeamDiscussionView', function () {
        var discussionView, createDiscussionView,
            testCourseID = 'course/1',
            testTeamDiscussionID = '12345';

        beforeEach(function () {
            setFixtures('<div class="discussion-module""></div>');
            $('.discussion-module').data('course-id', testCourseID);
            $('.discussion-module').data('discussion-id', testTeamDiscussionID);
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

        it('can render itself', function () {
            var requests = AjaxHelpers.requests(this),
                view = createDiscussionView(requests);
            expect(view.$('.discussion-thread').length).toEqual(3);
        });

        it('can create a new post', function () {
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
                content: TeamDiscussionSpecHelper.createMockThreadResponse({
                    id: "999", title: testTitle, body: testBody
                }),
                annotated_content_info: TeamDiscussionSpecHelper.createAnnotatedContentInfo()
            });

            // Expect the first thread to be the new post
            expect(view.$('.discussion-thread').length).toEqual(4);
            newThreadElement = $(view.$('.discussion-thread')[0]);
            expect(newThreadElement.find('.post-header-content h1').text().trim()).toEqual(testTitle);
            expect(newThreadElement.find('.post-body').text().trim()).toEqual(testBody);
        });
    });
});
