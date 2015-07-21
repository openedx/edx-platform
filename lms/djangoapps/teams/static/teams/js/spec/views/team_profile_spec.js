define([
    'underscore', 'common/js/spec_helpers/ajax_helpers', 'teams/js/models/team',
    'teams/js/views/team_profile', 'teams/js/spec_helpers/team_discussion_helpers',
    'xmodule_js/common_static/coffee/spec/discussion/discussion_spec_helper'
], function (_, AjaxHelpers, TeamModel, TeamProfileView, TeamDiscussionSpecHelper, DiscussionSpecHelper) {
    'use strict';
    describe('TeamProfileView', function () {
        var discussionView, createTeamProfileView,
            testCourseID = 'course/1',
            testTeamDiscussionID = '12345';

        beforeEach(function () {
            setFixtures('<div class="discussion-module""></div>');
            $('.discussion-module').data('course-id', testCourseID);
            $('.discussion-module').data('discussion-id', testTeamDiscussionID);
            DiscussionSpecHelper.setUnderscoreFixtures();
        });

        createTeamProfileView = function(requests) {
            var model = new TeamModel(
                { id: "test-team", name: "Test Team" },
                { parse: true }
            );
            discussionView = new TeamProfileView({
                el: '.discussion-module',
                courseID: testCourseID,
                model: model
            });
            discussionView.render();
            AjaxHelpers.expectRequest(
                requests,
                'GET',
                '/courses/course/1/discussion/forum/7065c53dcac4fe469fb66997da075f9af7e760a9/inline?page=1&ajax=1'
            );
            AjaxHelpers.respondWithJson(requests, TeamDiscussionSpecHelper.createMockDiscussionResponse());
            return discussionView;
        };

        it('can render itself', function () {
            var requests = AjaxHelpers.requests(this),
                view = createTeamProfileView(requests);
            expect(view.$('.discussion-thread').length).toEqual(3);
        });
    });
});
