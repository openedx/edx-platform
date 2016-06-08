define(['jquery', 'backbone', 'discussion/js/discussion_profile_page_factory'],
    function($, Backbone, DiscussionProfilePageFactory) {
        'use strict';

        describe('Discussion Profile Page Factory', function() {
            var initializeDiscussionProfilePageFactory = function(options) {
                DiscussionProfilePageFactory(options || {});
            };

            beforeEach(function() {
                // setFixtures('<section class="teams-content"></section>');
                // PageHelpers.preventBackboneChangingUrl();
            });

            afterEach(function() {
                // Backbone.history.stop();
                // $(document).off('ajaxError', TeamsTabView.prototype.errorHandler);
            });

            it('can render the "Teams" tab', function() {
                initializeDiscussionProfilePageFactory();
                expect($('.teams-content').text()).toContain('See all teams in your course, organized by topic');
            });
        });
    }
);
