define([
    'common/js/spec_helpers/ajax_helpers', 'teams/js/collections/topic', 'teams/js/views/topics'
], function (AjaxHelpers, TopicCollection, TopicsView) {
    'use strict';
    describe('TopicsView', function () {
        var initialTopics, topicCollection, topicsView, nextPageButtonCss;

        nextPageButtonCss = '.next-page-link';

        function generateTopics(startIndex, stopIndex) {
            return _.map(_.range(startIndex, stopIndex + 1), function (i) {
                return {
                    "description": "description " + i,
                    "name": "topic " + i,
                    "id": "id " + i,
                    "team_count": 0
                };
            });
        }

        beforeEach(function () {
            setFixtures('<div class="topics-container"></div>');
            initialTopics = generateTopics(1, 5);
            topicCollection = new TopicCollection(
                {
                    "count": 6,
                    "num_pages": 2,
                    "current_page": 1,
                    "start": 0,
                    "results": initialTopics
                },
                {course_id: 'my/course/id', parse: true}
            );
            topicsView = new TopicsView({el: '.topics-container', collection: topicCollection}).render();
        });

        /**
         * Verify that the topics view's header reflects the page we're currently viewing.
         * @param matchString the header we expect to see
         */
        function expectHeader(matchString) {
            expect(topicsView.$('.topics-paging-header').text()).toMatch(matchString);
        }

        /**
         * Verify that the topics list view renders the expected topics
         * @param expectedTopics an array of topic objects we expect to see
         */
        function expectTopics(expectedTopics) {
            var topicCards;
            topicCards = topicsView.$('.topic-card');
            _.each(expectedTopics, function (topic, index) {
                var currentCard = topicCards.eq(index);
                expect(currentCard.text()).toMatch(topic.name);
                expect(currentCard.text()).toMatch(topic.description);
                expect(currentCard.text()).toMatch(topic.team_count + ' Teams');
            });
        }

        /**
         * Verify that the topics footer reflects the current pagination
         * @param options a parameters hash containing:
         *  - currentPage: the one-indexed page we expect to be viewing
         *  - totalPages: the total number of pages to page through
         *  - isHidden: whether the footer is expected to be visible
         */
        function expectFooter(options) {
            var footerEl = topicsView.$('.topics-paging-footer');
            expect(footerEl.text())
                .toMatch(new RegExp(options.currentPage + '\\s+out of\\s+\/\\s+' + topicCollection.totalPages));
            expect(footerEl.hasClass('hidden')).toBe(options.isHidden);
        }

        it('can render the first of many pages', function () {
            expectHeader('Showing 1-5 out of 6 total');
            expectTopics(initialTopics);
            expectFooter({currentPage: 1, totalPages: 2, isHidden: false});
        });

        it('can render the only page', function () {
            initialTopics = generateTopics(1, 1);
            topicCollection.set(
                {
                    "count": 1,
                    "num_pages": 1,
                    "current_page": 1,
                    "start": 0,
                    "results": initialTopics
                },
                {parse: true}
            );
            expectHeader('Showing 1 out of 1 total');
            expectTopics(initialTopics);
            expectFooter({currentPage: 1, totalPages: 1, isHidden: true});
        });

        it('can change to the next page', function () {
            var requests = AjaxHelpers.requests(this),
                newTopics = generateTopics(1, 1);
            expectHeader('Showing 1-5 out of 6 total');
            expectTopics(initialTopics);
            expectFooter({currentPage: 1, totalPages: 2, isHidden: false});
            expect(requests.length).toBe(0);
            topicsView.$(nextPageButtonCss).click();
            expect(requests.length).toBe(1);
            AjaxHelpers.respondWithJson(requests, {
                "count": 6,
                "num_pages": 2,
                "current_page": 2,
                "start": 5,
                "results": newTopics
            });
            expectHeader('Showing 6-6 out of 6 total');
            expectTopics(newTopics);
            expectFooter({currentPage: 2, totalPages: 2, isHidden: false});
        });

        it('can change to the previous page', function () {
            var requests = AjaxHelpers.requests(this),
                previousPageTopics;
            initialTopics = generateTopics(1, 1);
            topicCollection.set(
                {
                    "count": 6,
                    "num_pages": 2,
                    "current_page": 2,
                    "start": 5,
                    "results": initialTopics
                },
                {parse: true}
            );
            expectHeader('Showing 6-6 out of 6 total');
            expectTopics(initialTopics);
            expectFooter({currentPage: 2, totalPages: 2, isHidden: false});
            topicsView.$('.previous-page-link').click();
            previousPageTopics = generateTopics(1, 5);
            AjaxHelpers.respondWithJson(requests, {
                "count": 6,
                "num_pages": 2,
                "current_page": 1,
                "start": 0,
                "results": previousPageTopics
            });
            expectHeader('Showing 1-5 out of 6 total');
            expectTopics(previousPageTopics);
            expectFooter({currentPage: 1, totalPages: 2, isHidden: false});
        });

        it('sets focus for screen readers', function () {
            var requests = AjaxHelpers.requests(this);
            spyOn($.fn, 'focus');
            topicsView.$(nextPageButtonCss).click();
            AjaxHelpers.respondWithJson(requests, {
                "count": 6,
                "num_pages": 2,
                "current_page": 2,
                "start": 5,
                "results": generateTopics(1, 1)
            });
            expect(topicsView.$('.sr-is-focusable').focus).toHaveBeenCalled();
        });

        it('does not change on server error', function () {
            var requests = AjaxHelpers.requests(this),
                expectInitialState = function () {
                    expectHeader('Showing 1-5 out of 6 total');
                    expectTopics(initialTopics);
                    expectFooter({currentPage: 1, totalPages: 2, isHidden: false});
                };
            expectInitialState();
            topicsView.$(nextPageButtonCss).click();
            requests[0].respond(500);
            expectInitialState();
        });
    });
});
