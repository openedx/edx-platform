define(['jquery', 'backbone', 'discussion/js/discussion_profile_page_factory'],
    function($, Backbone, DiscussionProfilePageFactory) {
        'use strict';

        describe('Discussion Profile Page Factory', function() {
            var testCourseId = 'test_course',
                initializeDiscussionProfilePageFactory = function(options) {
                options = _.extend({
                    courseId: testCourseId,
                    $el: $('.discussion-user-threads')
                });
                DiscussionProfilePageFactory(options || {});
            };

            beforeEach(function() {
                setFixtures('<div class="discussion-user-threads"></div>');
            });

            it('can render itself', function() {
                initializeDiscussionProfilePageFactory();
                expect($('.teams-content').text()).toContain('See all teams in your course, organized by topic');
            });
        });
    }
);
