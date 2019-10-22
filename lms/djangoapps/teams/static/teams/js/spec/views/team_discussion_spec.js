define([
    'underscore',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
    'common/js/spec_helpers/discussion_spec_helper',
    'teams/js/spec_helpers/team_spec_helpers',
    'teams/js/views/team_discussion'
], function(_, AjaxHelpers, DiscussionSpecHelper, TeamSpecHelpers, TeamDiscussionView) {
    'use strict';
    describe('TeamDiscussionView', function() {
        var discussionView, createDiscussionView;

        beforeEach(function() {
            setFixtures('<div class="discussion-module""></div>');
            $('.discussion-module').data('course-id', TeamSpecHelpers.testCourseID);
            $('.discussion-module').data('discussion-id', TeamSpecHelpers.testTeamDiscussionID);
            $('.discussion-module').data('user-create-comment', true);
            $('.discussion-module').data('user-create-subcomment', true);
            DiscussionSpecHelper.setUnderscoreFixtures();
        });

        createDiscussionView = function(requests, threads, errorStatus, errorBody) {
            discussionView = new TeamDiscussionView({
                el: '.discussion-module'
            });
            discussionView.render();
            if (errorStatus && errorBody) {
                AjaxHelpers.respondWithError(
                    requests,
                    errorStatus,
                    errorBody
                );
            } else {
                AjaxHelpers.respondWithJson(
                    requests,
                    TeamSpecHelpers.createMockDiscussionResponse(threads)
                );
            }
            return discussionView;
        };

        it('can render itself', function() {
            var requests = AjaxHelpers.requests(this),
                view = createDiscussionView(requests);
            expect(view.$('.forum-nav-thread-list .forum-nav-thread').length).toEqual(3);
        });

        it('cannot see discussion when user is not part of the team and discussion is set to be private', function() {
            var requests = AjaxHelpers.requests(this),
                errorMessage = 'Access to this thread is restricted to team members and staff.',
                view = createDiscussionView(
                    requests,
                    [],
                    403,
                    errorMessage
                );
            expect(view.$el.text().trim().replace(/"/g, '')).toEqual(errorMessage);
            expect($('.discussion-alert-wrapper p')
                .text()
                .trim()
                .replace(/"/g, '')
            ).toEqual(errorMessage);
        });
    });
});
