define([
    'common/js/spec_helpers/ajax_helpers', 'teams/js/collections/topic', 'teams/js/views/topics'
], function (AjaxHelpers, TopicCollection, TopicsView) {
    describe('TopicsView', function () {
        var initialTopics, topicCollection, topicsView;

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
         * Verify that the topics list view and footer reflects the page and topics states.
         * @param options a parameters hash containing:
         *  - expectedTopics: an array of topic objects we expect to see
         *  - currentPage: the one-indexed page we expect to be viewing
         *  - totalPages: the total number of pages to page through
         */
        function expectViewReflectsState(options) {
            var topicCards;
            // Verify the topics list
            topicCards = topicsView.$('.topic-card');
            _.each(options.expectedTopics, function (topic, index) {
                var currentCard = topicCards.eq(index);
                expect(currentCard.text()).toMatch(topic.name);
                expect(currentCard.text()).toMatch(topic.description);
                expect(currentCard.text()).toMatch(topic.team_count + ' Teams');
            });
            // Verify the footer
            expect(topicsView.$('.topics-paging-footer').text())
                .toMatch(new RegExp(options.currentPage + '\\s+out of\\s+\/\\s+' + topicCollection.totalPages));
        }

        it('can render the first of many pages', function () {
            expectHeader('Currently viewing 1 through 5 of 6 topics');
            expectViewReflectsState({expectedTopics: initialTopics, currentPage: 1, totalPages: 2});
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
            expectHeader('Currently viewing 1 topic');
            expectViewReflectsState({expectedTopics: initialTopics, currentPage: 1, totalPages: 1});
        });

        it('can change to the next page', function () {
            var requests = AjaxHelpers.requests(this),
                newTopics = generateTopics(1, 1);
            expectHeader('Currently viewing 1 through 5 of 6 topics');
            expectViewReflectsState({expectedTopics: initialTopics, currentPage: 1, totalPages: 2});
            expect(requests.length).toBe(0);
            topicsView.$('.next-page-link').click();
            expect(requests.length).toBe(1);
            AjaxHelpers.respondWithJson(requests, {
                "count": 6,
                "num_pages": 2,
                "current_page": 2,
                "start": 5,
                "results": newTopics
            });
            expectHeader('Currently viewing 6 through 6 of 6 topics');
            expectViewReflectsState({expectedTopics: newTopics, currentPage: 2, totalPages: 2});
        });

        it('can change to the previous page', function () {
            var requests = AjaxHelpers.requests(this);
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
            expectHeader('Currently viewing 6 through 6 of 6 topics');
            expectViewReflectsState({currentPage: 2, totalPages: 2});
            topicsView.$('.previous-page-link').click();
            var previousPageTopics = generateTopics(1, 5);
            AjaxHelpers.respondWithJson(requests, {
                "count": 6,
                "num_pages": 2,
                "current_page": 1,
                "start": 0,
                "results": previousPageTopics
            });
            expectHeader('Currently viewing 1 through 5 of 6 topics');
            expectViewReflectsState({currentPage: 1, totalPages: 2});
        });

        it('sets focus for screen readers', function () {
            var requests = AjaxHelpers.requests(this);
            spyOn($.fn, 'focus');
            topicsView.$('.next-page-link').click();
            AjaxHelpers.respondWithJson(requests, {
                "count": 6,
                "num_pages": 2,
                "current_page": 2,
                "start": 5,
                "results": generateTopics(1, 1)
            });
            expect(topicsView.$('.sr-is-focusable').focus).toHaveBeenCalled();
        });
    });
});
