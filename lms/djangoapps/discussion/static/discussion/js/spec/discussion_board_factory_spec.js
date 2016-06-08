define(['jquery', 'backbone', 'discussion/js/discussion_board_factory'],
    function($, Backbone, DiscussionBoardFactory) {
        'use strict';

        describe('Discussion Board Factory', function() {
            var initializeDiscussionBoardFactory = function() {
                DiscussionBoardFactory({});
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
                initializeDiscussionBoardFactory();
                expect($('.teams-content').text()).toContain('See all teams in your course, organized by topic');
            });
        });
    }
);
