/* globals Discussion */

define(
    [
        'underscore',
        'jquery',
        'backbone',
        'common/js/spec_helpers/discussion_spec_helper',
        'discussion/js/discussion_profile_page_factory'
    ],
    function(_, $, Backbone, DiscussionSpecHelper, DiscussionProfilePageFactory) {
        'use strict';

        describe('Discussion Profile Page Factory', function() {
            var testCourseId = 'test_course',
                initializeDiscussionProfilePageFactory = function(options) {
                    DiscussionProfilePageFactory(_.extend(
                        {
                            courseId: testCourseId,
                            roles: (options) ? options.roles : DiscussionSpecHelper.getTestRoleInfo(),
                            courseSettings: DiscussionSpecHelper.createTestCourseSettings().attributes,
                            el: $('.discussion-user-threads'),
                            discussion: new Discussion(),
                            userInfo: DiscussionSpecHelper.getTestUserInfo(),
                            sortPreference: null,
                            threads: [],
                            page: 1,
                            numPages: 5
                        },
                        options
                    ));
                };

            beforeEach(function() {
                setFixtures('<div class="discussion-user-threads"></div>');
                DiscussionSpecHelper.setUnderscoreFixtures();
            });

            it('can render itself', function() {
                initializeDiscussionProfilePageFactory();
                expect($('.discussion-user-threads').text()).toContain('Show');
            });
            it('can render itself when roles are undefined', function() {
                var options = {roles: undefined};
                initializeDiscussionProfilePageFactory(options);
                expect($('.discussion-user-threads').text()).toContain('Show');
            });
        });
    }
);
