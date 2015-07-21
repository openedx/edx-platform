define([
    'teams/js/views/team_discussion', 'common/js/spec_helpers/ajax_helpers'
], function (TeamDiscussionView, AjaxHelpers) {
    'use strict';
    describe('TeamDiscussionView', function () {
        var discussionView, initialTeams, createDiscussionView,
            testCourseID = 'course/1',
            testTeamDiscussionID = '12345';

        beforeEach(function () {
            setFixtures('<div class="discussion-module""></div>');
            $('.discussion-module').data('course-id', testCourseID);
            $('.discussion-module').data('discussion-id', testTeamDiscussionID);
        });

        createDiscussionView = function(requests) {
            discussionView = new TeamDiscussionView({
                el: '.discussion-module'
            });
            discussionView.render();
            AjaxHelpers.expectRequest(requests, 'GET', '/courses/course/1/discussion/forum/12345/inline?page=1&ajax=1');
            AjaxHelpers.respondWithJson(requests, {});
            return discussionView;
        };

        it('can render itself', function () {
            var requests = AjaxHelpers.requests(this),
                view = createDiscussionView(requests);
            expect(view.$('.discussion-thread').length).toEqual(1);
        });
    });
});
